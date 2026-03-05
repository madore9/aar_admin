import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Security
from fastapi_cache.decorator import cache

from app.cache import aar_key_builder
from app.databases.oracle_db import oracle_query
from app.databases.sqlite_db import execute_query
from app.schemas.course import Course, CourseSearchResponse, CourseUsageEntry
from app.utils.security import get_authenticated_user, KeyPermissions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])

# ---------------------------------------------------------------------------
# PeopleSoft SQL constants
#
# Filter: INSTITUTION = 'HRVRD' only. No career filter — CRSE_CAT_R3_VW is
# institution-level (matches PS AAR's own course list setup page behavior).
# Harvard uses school-based careers (HCOL, FAS, GSAS, ...) not UGRD/GRAD.
#
# Primary:  PS_CRSE_CAT_R3_VW — PS-delivered view, same source as AAR page.
# Fallback: Manual PS_CRSE_OFFER + PS_CRSE_CATALOG JOIN (if view inaccessible).
# Both return the same 5 columns mapping 1-to-1 to the Course Pydantic schema.
# ---------------------------------------------------------------------------

_VIEW_SELECT = """
    SELECT
        TRIM(V.CRSE_ID_SRCH)                                           AS system_id,
        TRIM(V.SUBJECT_SRCH) || ' ' || TRIM(V.CATALOG_NBR_SRCH)       AS id,
        V.COURSE_TITLE_LONG                                            AS title,
        TRIM(V.SUBJECT_SRCH)                                           AS department,
        V.UNITS_MINIMUM                                                AS credits
    FROM PS_CRSE_CAT_R3_VW V
    WHERE V.INSTITUTION     = 'HRVRD'
      AND V.COURSE_APPROVED = 'A'
"""

_MANUAL_SELECT = """
    SELECT
        TRIM(O.CRSE_ID)                                    AS system_id,
        TRIM(O.SUBJECT) || ' ' || TRIM(O.CATALOG_NBR)     AS id,
        C.COURSE_TITLE_LONG                                AS title,
        TRIM(O.SUBJECT)                                    AS department,
        C.UNITS_MINIMUM                                    AS credits
    FROM PS_CRSE_OFFER O
    JOIN PS_CRSE_CATALOG C
        ON  C.CRSE_ID = O.CRSE_ID
        AND C.EFFDT = (
            SELECT MAX(C2.EFFDT) FROM PS_CRSE_CATALOG C2
            WHERE C2.CRSE_ID    = C.CRSE_ID
              AND C2.EFFDT      <= SYSDATE
              AND C2.EFF_STATUS  = 'A'
        )
    WHERE O.INSTITUTION    = 'HRVRD'
      AND O.CRSE_OFFER_NBR = 1
      AND O.EFFDT = (
            SELECT MAX(O2.EFFDT) FROM PS_CRSE_OFFER O2
            WHERE O2.CRSE_ID = O.CRSE_ID AND O2.EFFDT <= SYSDATE
        )
"""

_COURSES_LIST_VIEW_BASE   = _VIEW_SELECT   + " ORDER BY V.SUBJECT_SRCH, V.CATALOG_NBR_SRCH FETCH FIRST 200 ROWS ONLY"
_COURSES_LIST_MANUAL_BASE = _MANUAL_SELECT + " ORDER BY O.SUBJECT, O.CATALOG_NBR FETCH FIRST 200 ROWS ONLY"

COURSE_LOOKUP_VIEW   = _VIEW_SELECT   + " AND V.CRSE_ID_SRCH = :system_id"
COURSE_LOOKUP_MANUAL = _MANUAL_SELECT + " AND O.CRSE_ID = :system_id"


def _build_search_filter_view(q: str, field: str) -> tuple[str, dict]:
    """Return (WHERE fragment, params dict) for view-based search."""
    q_pct = f"%{q}%"
    if field == "id":
        return (
            " AND UPPER(TRIM(V.SUBJECT_SRCH) || ' ' || TRIM(V.CATALOG_NBR_SRCH)) LIKE UPPER(:q)",
            {"q": q_pct},
        )
    if field == "title":
        return " AND UPPER(V.COURSE_TITLE_LONG) LIKE UPPER(:q)", {"q": q_pct}
    if field == "department":
        return " AND UPPER(TRIM(V.SUBJECT_SRCH)) LIKE UPPER(:q)", {"q": q_pct}
    # field == "all"
    return (
        " AND (UPPER(TRIM(V.SUBJECT_SRCH) || ' ' || TRIM(V.CATALOG_NBR_SRCH)) LIKE UPPER(:q)"
        "  OR  UPPER(V.COURSE_TITLE_LONG) LIKE UPPER(:q)"
        "  OR  UPPER(TRIM(V.SUBJECT_SRCH)) LIKE UPPER(:q))",
        {"q": q_pct},
    )


def _build_search_filter_manual(q: str, field: str) -> tuple[str, dict]:
    """Return (WHERE fragment, params dict) for manual-JOIN search."""
    q_pct = f"%{q}%"
    if field == "id":
        return (
            " AND UPPER(TRIM(O.SUBJECT) || ' ' || TRIM(O.CATALOG_NBR)) LIKE UPPER(:q)",
            {"q": q_pct},
        )
    if field == "title":
        return " AND UPPER(C.COURSE_TITLE_LONG) LIKE UPPER(:q)", {"q": q_pct}
    if field == "department":
        return " AND UPPER(TRIM(O.SUBJECT)) LIKE UPPER(:q)", {"q": q_pct}
    # field == "all"
    return (
        " AND (UPPER(TRIM(O.SUBJECT) || ' ' || TRIM(O.CATALOG_NBR)) LIKE UPPER(:q)"
        "  OR  UPPER(C.COURSE_TITLE_LONG) LIKE UPPER(:q)"
        "  OR  UPPER(TRIM(O.SUBJECT)) LIKE UPPER(:q))",
        {"q": q_pct},
    )


def _coerce_row(row: dict) -> dict:
    """Normalize Oracle row values for Pydantic Course model.

    Oracle may return Decimal for UNITS_MINIMUM; credits is typed as int.
    Also strips any trailing whitespace that TRIM() missed on Python side.
    """
    return {
        "system_id":  str(row.get("system_id", "") or "").strip(),
        "id":         str(row.get("id", "") or "").strip(),
        "title":      str(row.get("title", "") or "").strip(),
        "department": str(row.get("department", "") or "").strip(),
        "credits":    int(row.get("credits") or 0),
    }


async def _oracle_search(q: Optional[str], field: str) -> Optional[list[dict]]:
    """Try Oracle for course search. Returns:
    - list[dict]  → Oracle responded (may be empty if genuinely 0 results)
    - None        → Oracle pool is unavailable; caller should use SQLite
    """
    from app.databases import oracle_db
    if oracle_db._pool is None:
        return None  # Oracle not configured — skip to SQLite immediately

    # Try PS_CRSE_CAT_R3_VW first
    if q:
        where_frag, params = _build_search_filter_view(q, field)
        sql = _VIEW_SELECT + where_frag + " ORDER BY V.SUBJECT_SRCH, V.CATALOG_NBR_SRCH FETCH FIRST 200 ROWS ONLY"
    else:
        sql, params = _COURSES_LIST_VIEW_BASE, {}

    rows = await oracle_query(sql, params)
    if rows:
        return rows

    # View returned nothing or had an access error — try manual JOIN
    if q:
        where_frag_m, params_m = _build_search_filter_manual(q, field)
        sql_m = _MANUAL_SELECT + where_frag_m + " ORDER BY O.SUBJECT, O.CATALOG_NBR FETCH FIRST 200 ROWS ONLY"
    else:
        sql_m, params_m = _COURSES_LIST_MANUAL_BASE, {}

    rows_m = await oracle_query(sql_m, params_m)
    return rows_m  # [] if both failed, non-empty if manual JOIN succeeded


@router.get(
    "/",
    response_model=CourseSearchResponse,
    description=f"List or search courses. Requires key permission: `{KeyPermissions.READ_COURSES.value}`",
)
@cache(expire=600, namespace="courses", key_builder=aar_key_builder)
async def search_courses(
    q: str = Query(None, description="Search query"),
    field: str = Query("all", description="Search field: all, id, title, department"),
    user=Security(get_authenticated_user, scopes=[KeyPermissions.READ_COURSES]),
):
    """List/search courses. Oracle path first, SQLite seed data as fallback."""
    logger.info(f"search_courses called, q={q}, field={field}")

    valid_fields = ["all", "id", "title", "department", "system_id"]
    if field not in valid_fields:
        field = "all"

    # --- Path 1: PeopleSoft Oracle ---
    ps_rows = await _oracle_search(q, field)
    if ps_rows is not None:
        courses = [Course(**_coerce_row(r)) for r in ps_rows]
        logger.info(f"search_courses: {len(courses)} courses from Oracle")
        return CourseSearchResponse(courses=courses, total=len(courses))

    # --- Path 2: SQLite seed data fallback ---
    logger.info("search_courses: Oracle unavailable, using SQLite fallback")
    if q:
        if field == "all":
            where_clause = "WHERE id LIKE ? OR title LIKE ? OR department LIKE ? OR system_id LIKE ?"
            params = [f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"]
        elif field == "id":
            where_clause, params = "WHERE id LIKE ?", [f"%{q}%"]
        elif field == "title":
            where_clause, params = "WHERE title LIKE ?", [f"%{q}%"]
        elif field == "department":
            where_clause, params = "WHERE department LIKE ?", [f"%{q}%"]
        elif field == "system_id":
            where_clause, params = "WHERE system_id LIKE ?", [f"%{q}%"]
        else:
            where_clause, params = "", []
        courses_data = await execute_query(f"SELECT * FROM courses {where_clause} ORDER BY id", params)
    else:
        courses_data = await execute_query("SELECT * FROM courses ORDER BY id")

    courses = [Course(**c) for c in courses_data]
    return CourseSearchResponse(courses=courses, total=len(courses))


@router.get(
    "/{system_id}",
    response_model=Course,
    description=f"Get a single course by system_id. Requires key permission: `{KeyPermissions.READ_COURSES.value}`",
)
@cache(expire=1800, namespace="courses", key_builder=aar_key_builder)
async def get_course(
    system_id: str,
    user=Security(get_authenticated_user, scopes=[KeyPermissions.READ_COURSES]),
):
    """Get a single course by system_id. Oracle path first, SQLite fallback."""
    logger.info(f"get_course called, system_id={system_id}")

    # --- Path 1: PeopleSoft Oracle ---
    from app.databases import oracle_db
    if oracle_db._pool is not None:
        rows = await oracle_query(COURSE_LOOKUP_VIEW, {"system_id": system_id})
        if not rows:
            rows = await oracle_query(COURSE_LOOKUP_MANUAL, {"system_id": system_id})
        if rows:
            logger.info(f"get_course: found {system_id} in Oracle")
            return Course(**_coerce_row(rows[0]))
        raise HTTPException(status_code=404, detail="Course not found")

    # --- Path 2: SQLite seed data fallback ---
    logger.info(f"get_course: Oracle unavailable, SQLite fallback for {system_id}")
    course_data = await execute_query(
        "SELECT * FROM courses WHERE system_id = ?",
        [system_id],
        fetch_one=True,
    )
    if not course_data:
        raise HTTPException(status_code=404, detail="Course not found")
    return Course(**course_data)


@router.get(
    "/{system_id}/usage",
    response_model=list[CourseUsageEntry],
    description=f"Get all plans/requirements using this course. Requires key permission: `{KeyPermissions.READ_COURSES.value}`",
)
async def get_course_usage(
    system_id: str,
    user=Security(get_authenticated_user, scopes=[KeyPermissions.READ_COURSES]),
):
    """Get where this course appears across all plans.

    Always reads requirement_courses from SQLite — usage data is stored locally
    regardless of whether the course catalog comes from Oracle or seed data.
    """
    logger.info(f"get_course_usage called, system_id={system_id}")

    # Resolve the course catalog id (SUBJECT CATALOG_NBR) for wildcard matching
    course = await execute_query(
        "SELECT * FROM courses WHERE system_id = ?",
        [system_id],
        fetch_one=True,
    )
    course_catalog_id = course["id"] if course else None

    # If not in SQLite seed, try Oracle to get the catalog id
    if course_catalog_id is None:
        from app.databases import oracle_db
        if oracle_db._pool is not None:
            rows = await oracle_query(COURSE_LOOKUP_VIEW, {"system_id": system_id})
            if not rows:
                rows = await oracle_query(COURSE_LOOKUP_MANUAL, {"system_id": system_id})
            if rows:
                course_catalog_id = _coerce_row(rows[0])["id"]

    if course_catalog_id is None:
        raise HTTPException(status_code=404, detail="Course not found")

    exact_matches = await execute_query(
        """SELECT rc.*, r.title as req_title, r.id as req_id, r.plan_id,
                  ap.name as plan_name, ap.type as plan_type
           FROM requirement_courses rc
           JOIN requirements r ON rc.requirement_id = r.id
           JOIN academic_plans ap ON r.plan_id = ap.id
           WHERE rc.identifier = ?""",
        [system_id],
    )

    wildcard_entries = await execute_query(
        """SELECT rc.*, r.title as req_title, r.id as req_id, r.plan_id,
                  ap.name as plan_name, ap.type as plan_type
           FROM requirement_courses rc
           JOIN requirements r ON rc.requirement_id = r.id
           JOIN academic_plans ap ON r.plan_id = ap.id
           WHERE rc.is_wildcard = 1""",
    )

    results = []
    seen = set()

    for match in exact_matches:
        key = (match["plan_id"], match["req_id"], match["identifier"])
        if key not in seen:
            seen.add(key)
            results.append(
                {
                    "plan_name": match["plan_name"],
                    "plan_id": match["plan_id"],
                    "plan_type": match["plan_type"],
                    "requirement_title": match["req_title"],
                    "requirement_id": match["req_id"],
                    "matched_by": match["identifier"],
                    "is_excluded": bool(match["is_excluded"]),
                }
            )

    for wc in wildcard_entries:
        pattern = wc["identifier"]
        regex_pattern = "^" + pattern.replace("#", ".").replace("*", ".*") + "$"
        if re.match(regex_pattern, course_catalog_id):
            key = (wc["plan_id"], wc["req_id"], wc["identifier"])
            if key not in seen:
                seen.add(key)
                results.append(
                    {
                        "plan_name": wc["plan_name"],
                        "plan_id": wc["plan_id"],
                        "plan_type": wc["plan_type"],
                        "requirement_title": wc["req_title"],
                        "requirement_id": wc["req_id"],
                        "matched_by": wc["identifier"],
                        "is_excluded": bool(wc["is_excluded"]),
                    }
                )

    return results

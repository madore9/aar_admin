#!/usr/bin/env python3
"""
Manual Oracle connectivity and data validation script.

NOT a pytest test — run directly when ORACLE_DSN is configured to verify
that real PeopleSoft data flows correctly through the AAR Admin endpoints.

Usage:
    cd fastapi
    export ORACLE_DSN="10.138.149.157:1521/c9pr2"
    export ORACLE_USER="your_user"
    export ORACLE_PASSWORD="your_password"
    python -m tests.validate_oracle

Expected output on success:
    ✓  Oracle pool initialized
    ✓  PS_CRSE_CAT_R3_VW accessible — N rows for HRVRD
    ✓  Sample search results (first 5):
        COMPSCI 50  — Introduction to Computer Science (4 credits)
        ...
    ✓  Single course lookup: COMPSCI 50
    ✓  All 5 schema fields present in response
    ✓  Credits coerced to int: 4

If PS_CRSE_CAT_R3_VW is inaccessible, the script falls back to manual JOIN
and reports which path succeeded.
"""
import asyncio
import os
import sys

# Allow running as: python -m tests.validate_oracle from the fastapi/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.databases.oracle_db import init_oracle_pool, oracle_query, close_oracle_pool
from app.routers.courses import (
    _VIEW_SELECT,
    _MANUAL_SELECT,
    COURSE_LOOKUP_VIEW,
    COURSE_LOOKUP_MANUAL,
    _coerce_row,
)

PASS = "✓ "
FAIL = "✗ "
WARN = "⚠ "


async def main() -> int:
    """Run all validation checks. Returns 0 on success, 1 on any failure."""
    errors = 0

    # ------------------------------------------------------------------
    # 1. Pool init
    # ------------------------------------------------------------------
    oracle_dsn = os.environ.get("ORACLE_DSN", "")
    if not oracle_dsn:
        print(f"{FAIL} ORACLE_DSN is not set. Set ORACLE_DSN, ORACLE_USER, ORACLE_PASSWORD and re-run.")
        return 1

    await init_oracle_pool()

    from app.databases import oracle_db
    if oracle_db._pool is None:
        print(f"{FAIL} Oracle pool init failed. Check DSN, credentials, and network access to {oracle_dsn}")
        return 1

    print(f"{PASS} Oracle pool initialized ({oracle_dsn})")

    # ------------------------------------------------------------------
    # 2. Count rows via PS_CRSE_CAT_R3_VW
    # ------------------------------------------------------------------
    view_sql = "SELECT COUNT(*) AS cnt FROM PS_CRSE_CAT_R3_VW WHERE INSTITUTION = 'HRVRD' AND COURSE_APPROVED = 'A'"
    rows = await oracle_query(view_sql)
    if rows:
        cnt = rows[0].get("cnt", 0)
        print(f"{PASS} PS_CRSE_CAT_R3_VW accessible — {cnt:,} active HRVRD courses")
        use_view = True
    else:
        print(f"{WARN} PS_CRSE_CAT_R3_VW returned nothing or inaccessible — trying manual JOIN")
        use_view = False

    # ------------------------------------------------------------------
    # 3. Sample search (first 5 courses)
    # ------------------------------------------------------------------
    if use_view:
        sample_sql = _VIEW_SELECT + " ORDER BY V.SUBJECT_SRCH, V.CATALOG_NBR_SRCH FETCH FIRST 5 ROWS ONLY"
    else:
        sample_sql = _MANUAL_SELECT + " ORDER BY O.SUBJECT, O.CATALOG_NBR FETCH FIRST 5 ROWS ONLY"

    sample_rows = await oracle_query(sample_sql)
    if sample_rows:
        print(f"{PASS} Sample search results (first 5):")
        for r in sample_rows:
            r = _coerce_row(r)
            print(f"      {r['id']:<20}  {r['title'][:50]:<50}  ({r['credits']} credits)")
    else:
        print(f"{FAIL} Sample query returned no rows")
        errors += 1

    # ------------------------------------------------------------------
    # 4. Keyword search
    # ------------------------------------------------------------------
    if use_view:
        search_sql = (
            _VIEW_SELECT
            + " AND UPPER(V.COURSE_TITLE_LONG) LIKE UPPER('%CALCULUS%')"
            + " ORDER BY V.SUBJECT_SRCH, V.CATALOG_NBR_SRCH FETCH FIRST 3 ROWS ONLY"
        )
    else:
        search_sql = (
            _MANUAL_SELECT
            + " AND UPPER(C.COURSE_TITLE_LONG) LIKE UPPER('%CALCULUS%')"
            + " ORDER BY O.SUBJECT, O.CATALOG_NBR FETCH FIRST 3 ROWS ONLY"
        )

    search_rows = await oracle_query(search_sql)
    if search_rows:
        print(f"{PASS} Keyword search 'calculus' → {len(search_rows)} result(s): "
              f"{', '.join(_coerce_row(r)['id'] for r in search_rows)}")
    else:
        print(f"{WARN} Keyword search 'calculus' returned 0 results (may be correct)")

    # ------------------------------------------------------------------
    # 5. Single course lookup
    # ------------------------------------------------------------------
    if sample_rows:
        target_id = _coerce_row(sample_rows[0])["system_id"]
        lookup_sql = COURSE_LOOKUP_VIEW if use_view else COURSE_LOOKUP_MANUAL
        lookup_rows = await oracle_query(lookup_sql, {"system_id": target_id})
        if lookup_rows:
            r = _coerce_row(lookup_rows[0])
            print(f"{PASS} Single course lookup (system_id={target_id}): {r['id']}")
        else:
            print(f"{FAIL} Single lookup returned nothing for system_id={target_id}")
            errors += 1

    # ------------------------------------------------------------------
    # 6. Schema field coverage
    # ------------------------------------------------------------------
    if sample_rows:
        r = _coerce_row(sample_rows[0])
        required_fields = {"system_id", "id", "title", "department", "credits"}
        missing = required_fields - r.keys()
        if missing:
            print(f"{FAIL} Missing schema fields: {missing}")
            errors += 1
        else:
            print(f"{PASS} All 5 schema fields present: {list(r.keys())}")

    # ------------------------------------------------------------------
    # 7. Credits type check
    # ------------------------------------------------------------------
    if sample_rows:
        r = _coerce_row(sample_rows[0])
        if isinstance(r["credits"], int):
            print(f"{PASS} Credits coerced to int: {r['credits']}")
        else:
            print(f"{FAIL} Credits is {type(r['credits']).__name__}, expected int")
            errors += 1

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    await close_oracle_pool()

    print()
    if errors == 0:
        print("All checks passed ✓")
        return 0
    else:
        print(f"{errors} check(s) FAILED ✗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

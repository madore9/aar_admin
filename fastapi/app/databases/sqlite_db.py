import aiosqlite
from app.configs.config import DATABASE_PATH

_db = None

async def get_db():
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DATABASE_PATH)
        _db.row_factory = aiosqlite.Row
    return _db

async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None

async def check_health():
    try:
        db = await get_db()
        await db.execute("SELECT 1")
        return True
    except Exception:
        return False

async def execute_query(sql, params=None, fetch_one=False):
    db = await get_db()
    cursor = await db.execute(sql, params or [])
    if fetch_one:
        row = await cursor.fetchone()
        return dict(row) if row else None
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]

async def execute_write(sql, params=None):
    db = await get_db()
    cursor = await db.execute(sql, params or [])
    await db.commit()
    return cursor.lastrowid

async def init_db():
    """Create tables on startup."""
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS courses (
            system_id TEXT PRIMARY KEY,
            id TEXT NOT NULL,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            credits INTEGER NOT NULL DEFAULT 4
        );

        CREATE TABLE IF NOT EXISTS academic_plans (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            last_updated TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS requirements (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            required_courses_count INTEGER NOT NULL DEFAULT 0,
            required_units INTEGER NOT NULL DEFAULT 0,
            minimum_gpa REAL,
            course_list_id TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (plan_id) REFERENCES academic_plans(id)
        );

        CREATE TABLE IF NOT EXISTS requirement_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requirement_id TEXT NOT NULL,
            identifier TEXT NOT NULL,
            is_wildcard INTEGER NOT NULL DEFAULT 0,
            is_excluded INTEGER NOT NULL DEFAULT 0,
            include_equivalent_courses INTEGER NOT NULL DEFAULT 0,
            validity_type TEXT NOT NULL DEFAULT 'ALWAYS',
            valid_terms TEXT,
            valid_from TEXT,
            valid_to TEXT,
            FOREIGN KEY (requirement_id) REFERENCES requirements(id),
            UNIQUE(requirement_id, identifier)
        );

        CREATE TABLE IF NOT EXISTS course_lists (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS course_list_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_list_id TEXT NOT NULL,
            identifier TEXT NOT NULL,
            is_wildcard INTEGER NOT NULL DEFAULT 0,
            validity_type TEXT NOT NULL DEFAULT 'ALWAYS',
            valid_terms TEXT,
            FOREIGN KEY (course_list_id) REFERENCES course_lists(id),
            UNIQUE(course_list_id, identifier)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            user TEXT NOT NULL,
            action TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id TEXT NOT NULL,
            requirement_id TEXT NOT NULL,
            changes_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(plan_id, requirement_id)
        );
    """)
    await db.commit()

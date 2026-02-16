from fastapi import APIRouter
from app.routers import plans, courses, course_lists, audit_log

BASE_URL = "/aar"
router = APIRouter(prefix=BASE_URL)
router.include_router(plans.router)
router.include_router(courses.router)
router.include_router(course_lists.router)
router.include_router(audit_log.router)

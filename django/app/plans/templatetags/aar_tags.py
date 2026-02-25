"""
Custom template tags/filters for AAR Admin.

Mirrors my.harvard pattern of feature-specific template tag modules
(user_tags.py, course_tags.py, date_tags.py, etc.). This module
provides AAR-specific formatting filters.

Usage in templates:
    {% load aar_tags %}
    {{ plan.last_updated|format_date }}
    {{ user_role|role_display }}
    {{ plan.type|plan_type_badge }}
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def format_date(value):
    """
    Format an ISO date string for display.
    '2024-01-15' → 'Jan 15, 2024'
    """
    if not value:
        return ''
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt.strftime('%b %d, %Y')
    except (ValueError, TypeError):
        return str(value)


@register.filter
def role_display(role):
    """
    Human-friendly role name.
    'ADMIN_USER' → 'Administrator'
    'DEPT_USER'  → 'Department User'
    """
    mapping = {
        'ADMIN_USER': 'Administrator',
        'DEPT_USER': 'Department User',
    }
    return mapping.get(role, role)


@register.filter
def plan_type_badge_class(plan_type):
    """
    CSS classes for plan type badge styling.
    Returns Tailwind classes matching the portal design system.
    """
    classes = {
        'Concentration': 'bg-myh-100 text-myh-800',
        'Concentration - Honors': 'bg-amber-100 text-amber-800',
        'Secondary Field': 'bg-sky-100 text-sky-800',
        'Joint Concentration': 'bg-emerald-100 text-emerald-800',
    }
    return classes.get(plan_type, 'bg-gray-100 text-gray-800')


@register.filter
def truncate_id(value, length=8):
    """Truncate a UUID or long ID for display."""
    s = str(value)
    if len(s) > length:
        return s[:length] + '…'
    return s

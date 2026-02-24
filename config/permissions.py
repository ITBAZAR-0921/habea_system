from functools import wraps

from django.contrib.auth.models import Group
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden

ROLE_GROUPS = {
    'system_admin': 'Систем админ',
    'hse_manager': 'ХАБЭА менежер',
    'department_head': 'Хэлтсийн дарга',
    'employee': 'Ажилтан',
}
MANAGER_ROLES = ('system_admin', 'hse_manager', 'department_head')


def ensure_role_groups():
    for group_name in ROLE_GROUPS:
        Group.objects.get_or_create(name=group_name)


def get_user_role(user):
    if user.is_superuser:
        return 'system_admin'
    group = user.groups.filter(name__in=ROLE_GROUPS.keys()).values_list('name', flat=True).first()
    return group or 'employee'


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if get_user_role(request.user) in allowed_roles:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden('Таны эрх хүрэхгүй байна.')

        return _wrapped_view

    return decorator

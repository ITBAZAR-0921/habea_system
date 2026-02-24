from .permissions import get_user_role


MANAGER_ROLES = {'system_admin', 'hse_manager', 'department_head'}


def role_context(request):
    role = None
    if request.user.is_authenticated:
        role = get_user_role(request.user)

    return {
        'current_role': role,
        'is_manager_role': role in MANAGER_ROLES,
        'is_employee_role': role == 'employee',
    }

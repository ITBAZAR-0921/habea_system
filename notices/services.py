from django.db.models import Q

from employees.models import Department
from employees.models import Employee

from .models import Notice, NoticeRead


def get_department_ancestor_ids(department):
    ancestor_ids = set()
    current = department
    while current is not None:
        ancestor_ids.add(current.id)
        current = current.parent
    return ancestor_ids


def get_target_employees_for_notice(notice):
    qs = Employee.objects.select_related('department', 'position').all()

    if notice.notice_type == Notice.NoticeType.ORGANIZATION_WIDE:
        return qs
    if notice.notice_type == Notice.NoticeType.DEPARTMENT:
        selected_ids = list(notice.departments.values_list('id', flat=True))
        if not selected_ids:
            return qs.none()

        all_ids = set(selected_ids)
        queue = list(selected_ids)
        while queue:
            current_id = queue.pop()
            child_ids = list(Department.objects.filter(parent_id=current_id).values_list('id', flat=True))
            for child_id in child_ids:
                if child_id not in all_ids:
                    all_ids.add(child_id)
                    queue.append(child_id)
        return qs.filter(department_id__in=all_ids)
    if notice.notice_type == Notice.NoticeType.POSITION:
        return qs.filter(position__in=notice.positions.all())
    if notice.notice_type == Notice.NoticeType.SPECIFIC_EMPLOYEE:
        return qs.filter(id__in=notice.employees.values_list('id', flat=True))
    return qs.none()


def get_applicable_notices_for_employee(employee):
    department_ancestors = get_department_ancestor_ids(employee.department) if employee.department else set()
    position_id = employee.position_id

    filters = Q(notice_type=Notice.NoticeType.ORGANIZATION_WIDE)
    if department_ancestors:
        filters |= Q(notice_type=Notice.NoticeType.DEPARTMENT, departments__id__in=department_ancestors)
    if position_id:
        filters |= Q(notice_type=Notice.NoticeType.POSITION, positions__id=position_id)
    filters |= Q(notice_type=Notice.NoticeType.SPECIFIC_EMPLOYEE, employees=employee)

    return Notice.objects.filter(is_active=True).filter(filters).distinct().prefetch_related(
        'departments', 'positions', 'employees'
    )


def get_or_create_notice_read(employee, notice):
    return NoticeRead.objects.get_or_create(employee=employee, notice=notice)


def get_notice_metrics_for_dashboard():
    active_notices = Notice.objects.filter(is_active=True)

    unread_count = 0
    unacknowledged_count = 0

    for notice in active_notices:
        target_qs = get_target_employees_for_notice(notice)
        total_targets = target_qs.count()
        if total_targets == 0:
            continue

        reads = NoticeRead.objects.filter(notice=notice)
        read_ids = set(reads.values_list('employee_id', flat=True))
        acknowledged_ids = set(reads.filter(acknowledged=True).values_list('employee_id', flat=True))
        target_ids = set(target_qs.values_list('id', flat=True))

        unread_count += len(target_ids - read_ids)
        if notice.requires_acknowledgement:
            unacknowledged_count += len(target_ids - acknowledged_ids)

    return {
        'total_notices': active_notices.count(),
        'unread_notices': unread_count,
        'unacknowledged_notices': unacknowledged_count,
    }

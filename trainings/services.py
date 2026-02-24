from employees.models import Department, Employee

from .models import Training, TrainingParticipation


def _collect_department_with_children_ids(department_ids):
    ids = set(department_ids)
    queue = list(department_ids)

    while queue:
        current_id = queue.pop(0)
        child_ids = list(Department.objects.filter(parent_id=current_id).values_list('id', flat=True))
        for child_id in child_ids:
            if child_id not in ids:
                ids.add(child_id)
                queue.append(child_id)

    return ids


def get_target_employees_for_training(training):
    qs = Employee.objects.select_related('department', 'position').all()

    if training.training_type == Training.TrainingType.ORGANIZATION_WIDE:
        return qs

    if training.training_type == Training.TrainingType.DEPARTMENT:
        dept_ids = list(training.departments.values_list('id', flat=True))
        if not dept_ids:
            return qs.none()
        all_ids = _collect_department_with_children_ids(dept_ids)
        return qs.filter(department_id__in=all_ids)

    if training.training_type == Training.TrainingType.POSITION:
        return qs.filter(position__in=training.positions.all())

    if training.training_type == Training.TrainingType.SPECIFIC_EMPLOYEE:
        return qs.filter(id__in=training.employees.values_list('id', flat=True))

    return qs.none()


def sync_training_participations(training):
    target_ids = set(get_target_employees_for_training(training).values_list('id', flat=True))
    existing = {
        p.employee_id: p
        for p in TrainingParticipation.objects.filter(training=training)
    }

    create_list = []
    for employee_id in target_ids:
        if employee_id not in existing:
            create_list.append(
                TrainingParticipation(employee_id=employee_id, training=training)
            )

    if create_list:
        TrainingParticipation.objects.bulk_create(create_list)

    return {
        'created': len(create_list),
        'total_targets': len(target_ids),
    }

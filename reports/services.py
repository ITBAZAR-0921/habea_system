from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from django.db.models import Avg, Count, Prefetch, Q
from django.utils import timezone

from employees.models import Department, Employee, Position
from exams.models import Exam, ExamAttempt
from instructions.models import InstructionRecord
from notices.models import Notice, NoticeRead
from trainings.models import Training, TrainingParticipation


@dataclass(frozen=True)
class ReportFilters:
    start_date: date | None
    end_date: date | None
    department_id: int | None
    position_id: int | None


@dataclass(frozen=True)
class ReportScope:
    unrestricted: bool = True
    allowed_department_ids: frozenset[int] = frozenset()


def _collect_descendants_map() -> dict[int, set[int]]:
    children_map: dict[int | None, list[int]] = {}
    for item in Department.objects.only('id', 'parent_id'):
        children_map.setdefault(item.parent_id, []).append(item.id)

    descendants_map: dict[int, set[int]] = {}
    for item in Department.objects.only('id'):
        descendants: set[int] = set()
        stack = [item.id]
        while stack:
            current = stack.pop()
            descendants.add(current)
            stack.extend(children_map.get(current, []))
        descendants_map[item.id] = descendants
    return descendants_map


def get_department_and_children_ids(department_id: int) -> set[int]:
    descendants_map = _collect_descendants_map()
    return descendants_map.get(department_id, {department_id})


def _base_employee_queryset(filters: ReportFilters, scope: ReportScope):
    qs = Employee.objects.select_related('department', 'position').all()

    if not scope.unrestricted:
        if not scope.allowed_department_ids:
            return qs.none()
        qs = qs.filter(department_id__in=scope.allowed_department_ids)

    if filters.department_id:
        dept_ids = get_department_and_children_ids(filters.department_id)
        if not scope.unrestricted:
            dept_ids = dept_ids & set(scope.allowed_department_ids)
        if not dept_ids:
            return qs.none()
        qs = qs.filter(department_id__in=dept_ids)

    if filters.position_id:
        qs = qs.filter(position_id=filters.position_id)
    return qs


def _within_date_range(queryset, field: str, filters: ReportFilters):
    if filters.start_date:
        queryset = queryset.filter(**{f'{field}__date__gte': filters.start_date})
    if filters.end_date:
        queryset = queryset.filter(**{f'{field}__date__lte': filters.end_date})
    return queryset


def _round_percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator * 100.0) / denominator, 2)


def _build_employee_index(employees: list[Employee]) -> tuple[set[int], dict[int, dict[str, Any]], dict[int, set[int]], dict[int, set[int]]]:
    employee_ids = {item.id for item in employees}
    employee_map: dict[int, dict[str, Any]] = {}
    department_employee_ids: dict[int, set[int]] = {}
    position_employee_ids: dict[int, set[int]] = {}

    for item in employees:
        employee_map[item.id] = {
            'id': item.id,
            'name': f'{item.last_name} {item.first_name}',
            'department': item.department.name if item.department else '-',
            'position': item.position.name if item.position else '-',
        }
        if item.department_id:
            department_employee_ids.setdefault(item.department_id, set()).add(item.id)
        if item.position_id:
            position_employee_ids.setdefault(item.position_id, set()).add(item.id)

    return employee_ids, employee_map, department_employee_ids, position_employee_ids


def _target_employee_ids_for_notice(
    notice: Notice,
    base_employee_ids: set[int],
    descendants_map: dict[int, set[int]],
    department_employee_ids: dict[int, set[int]],
    position_employee_ids: dict[int, set[int]],
) -> set[int]:
    if notice.notice_type == Notice.NoticeType.ORGANIZATION_WIDE:
        return set(base_employee_ids)

    if notice.notice_type == Notice.NoticeType.DEPARTMENT:
        target_ids: set[int] = set()
        for department in notice.departments.all():
            dept_id = department.id
            for desc_id in descendants_map.get(dept_id, {dept_id}):
                target_ids |= department_employee_ids.get(desc_id, set())
        return target_ids & base_employee_ids

    if notice.notice_type == Notice.NoticeType.POSITION:
        target_ids: set[int] = set()
        for position in notice.positions.all():
            target_ids |= position_employee_ids.get(position.id, set())
        return target_ids & base_employee_ids

    if notice.notice_type == Notice.NoticeType.SPECIFIC_EMPLOYEE:
        selected = {employee.id for employee in notice.employees.all()}
        return selected & base_employee_ids

    return set()


def get_notice_report_data(
    filters: ReportFilters,
    scope: ReportScope,
    base_employees: list[Employee] | None = None,
) -> dict[str, Any]:
    today = timezone.localdate()
    due_limit = today + timedelta(days=30)

    employees = base_employees if base_employees is not None else list(_base_employee_queryset(filters, scope))
    base_employee_ids, employee_map, department_employee_ids, position_employee_ids = _build_employee_index(employees)
    descendants_map = _collect_descendants_map()

    notices = (
        Notice.objects.filter(is_active=True)
        .prefetch_related('departments', 'positions', 'employees', Prefetch('reads', queryset=NoticeRead.objects.all()))
        .order_by('-created_at')
    )
    notices = _within_date_range(notices, 'created_at', filters)

    total_targets = 0
    total_read = 0
    total_unread = 0
    total_unacknowledged = 0
    rows = []

    for notice in notices:
        target_ids = _target_employee_ids_for_notice(
            notice,
            base_employee_ids,
            descendants_map,
            department_employee_ids,
            position_employee_ids,
        )
        if not target_ids:
            continue

        read_objects = [item for item in notice.reads.all() if item.employee_id in target_ids]
        read_ids = {item.employee_id for item in read_objects}
        acknowledged_ids = {item.employee_id for item in read_objects if item.acknowledged}

        target_count = len(target_ids)
        read_count = len(read_ids)
        unread_count = max(target_count - read_count, 0)
        if notice.requires_acknowledgement:
            unack_count = max(target_count - len(acknowledged_ids), 0)
        else:
            unack_count = 0

        total_targets += target_count
        total_read += read_count
        total_unread += unread_count
        total_unacknowledged += unack_count

        drilldown = []
        for employee_id in sorted(target_ids):
            profile = employee_map.get(employee_id)
            if not profile:
                continue
            drilldown.append(
                {
                    **profile,
                    'is_read': employee_id in read_ids,
                    'is_acknowledged': employee_id in acknowledged_ids,
                }
            )

        rows.append(
            {
                'id': notice.id,
                'title': notice.title,
                'total_employees': target_count,
                'read_count': read_count,
                'unread_count': unread_count,
                'drilldown': drilldown,
            }
        )

    expires_qs = notices.exclude(expires_at__isnull=True)
    expired_count = expires_qs.filter(expires_at__lt=today).count()
    due_soon_count = expires_qs.filter(expires_at__gte=today, expires_at__lte=due_limit).count()

    metrics = {
        'total_notices': len(rows),
        'read_percent': _round_percent(total_read, total_targets),
        'unread_percent': _round_percent(total_unread, total_targets),
        'unacknowledged_percent': _round_percent(total_unacknowledged, total_targets),
        'expired_count': expired_count,
        'due_soon_count': due_soon_count,
    }

    return {
        'metrics': metrics,
        'rows': rows,
        'chart': {
            'labels': ['Танилцсан', 'Танилцаагүй', 'Баталгаажаагүй'],
            'values': [total_read, total_unread, total_unacknowledged],
        },
    }


def get_instruction_report_data(
    filters: ReportFilters,
    scope: ReportScope,
    base_employees: list[Employee] | None = None,
) -> dict[str, Any]:
    today = timezone.localdate()
    due_limit = today + timedelta(days=30)
    employees = base_employees if base_employees is not None else list(_base_employee_queryset(filters, scope))
    employee_ids = [item.id for item in employees]

    records = InstructionRecord.objects.select_related('instruction', 'employee').filter(employee_id__in=employee_ids)
    records = _within_date_range(records, 'created_at', filters)

    total_count = records.count()
    acknowledged_count = records.filter(acknowledged=True).count()
    overdue_count = records.filter(next_due_date__lt=today).count()
    due_soon_count = records.filter(next_due_date__gte=today, next_due_date__lte=due_limit).count()
    unack_count = records.filter(acknowledged=False).count()

    grouped = records.values('instruction_id', 'instruction__title').annotate(
        total_employees=Count('id'),
        acknowledged=Count('id', filter=Q(acknowledged=True)),
        overdue=Count('id', filter=Q(next_due_date__lt=today)),
        due_soon=Count('id', filter=Q(next_due_date__gte=today, next_due_date__lte=due_limit)),
    )

    rows = []
    for item in grouped.order_by('instruction__title'):
        rows.append(
            {
                'title': item['instruction__title'],
                'total_employees': item['total_employees'],
                'acknowledged': item['acknowledged'],
                'overdue': item['overdue'],
                'due_soon': item['due_soon'],
            }
        )

    return {
        'metrics': {
            'total_records': total_count,
            'acknowledged_count': acknowledged_count,
            'unacknowledged_count': unack_count,
            'overdue_count': overdue_count,
            'due_soon_count': due_soon_count,
        },
        'rows': rows,
        'chart': {
            'labels': ['Танилцсан', 'Танилцаагүй', 'Хугацаа дууссан'],
            'values': [acknowledged_count, unack_count, overdue_count],
        },
    }


def get_training_report_data(
    filters: ReportFilters,
    scope: ReportScope,
    base_employees: list[Employee] | None = None,
) -> dict[str, Any]:
    employees = base_employees if base_employees is not None else list(_base_employee_queryset(filters, scope))
    employee_ids = [item.id for item in employees]

    trainings = Training.objects.filter(is_active=True).order_by('-created_at')
    if filters.start_date:
        trainings = trainings.filter(start_date__gte=filters.start_date)
    if filters.end_date:
        trainings = trainings.filter(start_date__lte=filters.end_date)

    training_ids = list(trainings.values_list('id', flat=True))
    participations = TrainingParticipation.objects.filter(
        training_id__in=training_ids,
        employee_id__in=employee_ids,
    )

    overall_total = participations.count()
    overall_completed = participations.filter(status=TrainingParticipation.Status.COMPLETED).count()
    overall_incomplete = overall_total - overall_completed
    required_incomplete = participations.filter(training__required=True).exclude(
        status=TrainingParticipation.Status.COMPLETED
    ).count()

    grouped = participations.values('training_id').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status=TrainingParticipation.Status.COMPLETED)),
    )
    grouped_map = {item['training_id']: item for item in grouped}

    rows = []
    for training in trainings:
        stats = grouped_map.get(training.id, {'total': 0, 'completed': 0})
        total = stats['total']
        completed = stats['completed']
        incomplete = max(total - completed, 0)
        rows.append(
            {
                'title': training.title,
                'total_target': total,
                'completed_percent': _round_percent(completed, total),
                'incomplete_percent': _round_percent(incomplete, total),
            }
        )

    return {
        'metrics': {
            'total_trainings': trainings.count(),
            'completed_count': overall_completed,
            'incomplete_count': overall_incomplete,
            'required_incomplete_count': required_incomplete,
        },
        'rows': rows,
        'chart': {
            'labels': ['Дууссан', 'Дуусаагүй', 'Required боловч дуусаагүй'],
            'values': [overall_completed, overall_incomplete, required_incomplete],
        },
    }


def get_exam_report_data(
    filters: ReportFilters,
    scope: ReportScope,
    base_employees: list[Employee] | None = None,
) -> dict[str, Any]:
    employees = base_employees if base_employees is not None else list(_base_employee_queryset(filters, scope))
    employee_ids = [item.id for item in employees]

    exams = Exam.objects.filter(exam_type=Exam.ExamType.OFFICIAL, is_active=True).order_by('-created_at')
    exams = _within_date_range(exams, 'created_at', filters)

    attempts = ExamAttempt.objects.filter(
        exam_id__in=exams.values_list('id', flat=True),
        employee_id__in=employee_ids,
        completed_at__isnull=False,
    )
    attempts = _within_date_range(attempts, 'started_at', filters)

    total_taken = attempts.count()
    passed_count = attempts.filter(is_passed=True).count()
    failed_count = attempts.filter(is_passed=False).count()
    avg_score = attempts.aggregate(avg_score=Avg('total_score'))['avg_score'] or 0

    grouped = attempts.values('exam_id').annotate(
        total=Count('id'),
        average_score=Avg('total_score'),
        passed=Count('id', filter=Q(is_passed=True)),
        failed=Count('id', filter=Q(is_passed=False)),
    )
    grouped_map = {item['exam_id']: item for item in grouped}

    rows = []
    for exam in exams:
        item = grouped_map.get(exam.id, {'total': 0, 'average_score': 0, 'passed': 0, 'failed': 0})
        total = item['total']
        rows.append(
            {
                'title': exam.title,
                'participated': total,
                'avg_score': round((item['average_score'] or 0), 2),
                'passed_percent': _round_percent(item['passed'], total),
                'failed_percent': _round_percent(item['failed'], total),
            }
        )

    return {
        'metrics': {
            'total_exams': exams.count(),
            'total_taken': total_taken,
            'passed_percent': _round_percent(passed_count, total_taken),
            'failed_percent': _round_percent(failed_count, total_taken),
            'avg_score': round(avg_score, 2),
        },
        'rows': rows,
        'chart': {
            'labels': ['Тэнцсэн', 'Унасан'],
            'values': [passed_count, failed_count],
        },
    }


def get_filter_options(scope: ReportScope) -> dict[str, Any]:
    departments = Department.objects.order_by('name').all()
    positions = Position.objects.order_by('name').all()

    if not scope.unrestricted:
        departments = departments.filter(id__in=scope.allowed_department_ids)
        positions = positions.filter(employees__department_id__in=scope.allowed_department_ids).distinct()

    return {
        'departments': departments,
        'positions': positions,
    }


def build_reports_payload(filters: ReportFilters, scope: ReportScope) -> dict[str, Any]:
    base_employees = list(_base_employee_queryset(filters, scope))
    return {
        'notices': get_notice_report_data(filters, scope, base_employees),
        'instructions': get_instruction_report_data(filters, scope, base_employees),
        'trainings': get_training_report_data(filters, scope, base_employees),
        'exams': get_exam_report_data(filters, scope, base_employees),
    }

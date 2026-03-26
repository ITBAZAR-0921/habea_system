from __future__ import annotations

from datetime import datetime
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.views import View

from config.permissions import MANAGER_ROLES, get_user_role
from employees.models import Employee

from .exporters import export_tab_to_excel, export_tab_to_pdf
from .services import (
    ReportFilters,
    ReportScope,
    build_reports_payload,
    get_department_and_children_ids,
    get_filter_options,
)

VALID_TABS = {'notices', 'instructions', 'trainings', 'exams'}


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _parse_int(value: str | None):
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_filters(request):
    return ReportFilters(
        start_date=_parse_date(request.GET.get('start_date')),
        end_date=_parse_date(request.GET.get('end_date')),
        department_id=_parse_int(request.GET.get('department_id')),
        position_id=_parse_int(request.GET.get('position_id')),
    )


def _active_tab(request):
    tab = request.GET.get('tab', 'notices')
    return tab if tab in VALID_TABS else 'notices'


def _filter_query_for_template(request, tab: str):
    query = {
        'tab': tab,
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
        'department_id': request.GET.get('department_id', ''),
        'position_id': request.GET.get('position_id', ''),
    }
    return urlencode({k: v for k, v in query.items() if v not in {None, ''}})


class ReportPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = set(MANAGER_ROLES)

    def test_func(self):
        return get_user_role(self.request.user) in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return render(self.request, '403.html', status=403)

    def _build_scope(self) -> ReportScope:
        role = get_user_role(self.request.user)
        if role in {'system_admin', 'hse_manager'}:
            return ReportScope(unrestricted=True)

        employee = Employee.objects.select_related('department').filter(user=self.request.user).first()
        if employee is None or employee.department_id is None:
            return ReportScope(unrestricted=False, allowed_department_ids=frozenset())

        allowed_ids = get_department_and_children_ids(employee.department_id)
        return ReportScope(unrestricted=False, allowed_department_ids=frozenset(allowed_ids))


class ReportDashboardView(ReportPermissionMixin, View):
    def get(self, request):
        filters = _build_filters(request)
        active_tab = _active_tab(request)
        scope = self._build_scope()

        if filters.start_date and filters.end_date and filters.start_date > filters.end_date:
            messages.warning(request, 'Эхлэх огноо дуусах огнооноос их байж болохгүй.')

        payload = build_reports_payload(filters, scope)
        options = get_filter_options(scope)

        context = {
            'active_tab': active_tab,
            'reports_data': payload,
            'departments': options['departments'],
            'positions': options['positions'],
            'filters': {
                'start_date': request.GET.get('start_date', ''),
                'end_date': request.GET.get('end_date', ''),
                'department_id': request.GET.get('department_id', ''),
                'position_id': request.GET.get('position_id', ''),
            },
            'export_querystring': _filter_query_for_template(request, active_tab),
        }
        return render(request, 'reports/dashboard.html', context)


class ReportExportView(ReportPermissionMixin, View):
    def get(self, request):
        tab = _active_tab(request)
        export_format = request.GET.get('format', '').lower()
        filters = _build_filters(request)
        scope = self._build_scope()

        payload = build_reports_payload(filters, scope)
        tab_data = payload[tab]

        if export_format == 'excel':
            try:
                return export_tab_to_excel(tab, tab_data)
            except ImportError:
                return HttpResponseBadRequest('Excel export сан суулгагдаагүй байна.')
        if export_format == 'pdf':
            try:
                return export_tab_to_pdf(tab, tab_data)
            except ImportError:
                return HttpResponseBadRequest('PDF export сан суулгагдаагүй байна.')
        return HttpResponseBadRequest('Дэмжигдээгүй export төрөл байна.')

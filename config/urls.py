from django.contrib import admin, messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import Group, User
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render
from django.urls import include, path

from employees.models import Employee
from instructions.models import Instruction, InstructionRecord

from .forms import RoleAssignmentForm
from .permissions import ROLE_GROUPS, ensure_role_groups, get_user_role, role_required


@role_required(['system_admin', 'hse_manager', 'department_head', 'employee'])
def dashboard(request):
    records = InstructionRecord.objects.all()
    overdue_count = sum(1 for record in records if record.status == InstructionRecord.Status.OVERDUE)
    due_soon_count = sum(1 for record in records if record.status == InstructionRecord.Status.DUE_SOON)

    context = {
        'employee_count': Employee.objects.count(),
        'instruction_count': Instruction.objects.count(),
        'record_count': records.count(),
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count,
    }
    return render(request, 'dashboard.html', context)


@role_required(['system_admin', 'hse_manager', 'department_head'])
def reports(request):
    records = InstructionRecord.objects.select_related('employee', 'instruction').all()
    overdue_records = [record for record in records if record.status == InstructionRecord.Status.OVERDUE]
    due_soon_records = [record for record in records if record.status == InstructionRecord.Status.DUE_SOON]

    return render(
        request,
        'reports.html',
        {
            'overdue_records': overdue_records,
            'due_soon_records': due_soon_records,
        },
    )


@role_required(['system_admin'])
def settings_view(request):
    ensure_role_groups()

    if request.method == 'POST':
        form = RoleAssignmentForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            role = form.cleaned_data['role']

            user.groups.remove(*Group.objects.filter(name__in=ROLE_GROUPS.keys()))

            new_group = Group.objects.get(name=role)
            user.groups.add(new_group)
            messages.success(request, f'{user.username} хэрэглэгчийн эрхийг {ROLE_GROUPS[role]} болголоо.')
            return redirect('settings')
    else:
        form = RoleAssignmentForm()

    users = User.objects.all().order_by('username')
    user_roles = [(user, ROLE_GROUPS.get(get_user_role(user), 'Ажилтан')) for user in users]

    return render(
        request,
        'settings.html',
        {
            'form': form,
            'user_roles': user_roles,
        },
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', dashboard, name='dashboard'),
    path('employees/', include('employees.urls')),
    path('instructions/', include('instructions.urls')),
    path('reports/', reports, name='reports'),
    path('settings/', settings_view, name='settings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

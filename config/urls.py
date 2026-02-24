from datetime import timedelta

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin, messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect, render
from django.urls import include, path
from django.utils import timezone

from employees.models import Employee
from instructions.models import Instruction, InstructionRecord
from notices.services import get_notice_metrics_for_dashboard

from .forms import RoleAssignmentForm
from .permissions import MANAGER_ROLES, ROLE_GROUPS, ensure_role_groups, get_user_role, role_required



def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if get_user_role(request.user) == 'employee':
        return redirect('my_notices')
    return redirect('dashboard')


@role_required(MANAGER_ROLES)
def dashboard(request):
    today = timezone.localdate()
    due_limit = today + timedelta(days=30)

    records = InstructionRecord.objects.all()
    overdue_count = records.filter(next_due_date__lt=today).count()
    due_soon_count = records.filter(next_due_date__gte=today, next_due_date__lte=due_limit).count()
    unacknowledged_count = records.filter(acknowledged=False).count()

    notice_metrics = get_notice_metrics_for_dashboard()

    context = {
        'employee_count': Employee.objects.count(),
        'instruction_count': Instruction.objects.count(),
        'record_count': records.count(),
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count,
        'unacknowledged_count': unacknowledged_count,
        'total_notice_count': notice_metrics['total_notices'],
        'unread_notice_count': notice_metrics['unread_notices'],
        'unacknowledged_notice_count': notice_metrics['unacknowledged_notices'],
    }
    return render(request, 'dashboard.html', context)


@role_required(MANAGER_ROLES)
def reports(request):
    today = timezone.localdate()
    due_limit = today + timedelta(days=30)

    records = InstructionRecord.objects.select_related('employee', 'instruction').all()
    overdue_records = records.filter(next_due_date__lt=today)
    due_soon_records = records.filter(next_due_date__gte=today, next_due_date__lte=due_limit)
    unacknowledged_records = records.filter(acknowledged=False)

    return render(
        request,
        'reports.html',
        {
            'overdue_records': overdue_records,
            'due_soon_records': due_soon_records,
            'unacknowledged_records': unacknowledged_records,
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
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('employees/', include('employees.urls')),
    path('instructions/', include('instructions.urls')),
    path('notices/', include('notices.urls')),
    path('trainings/', include('trainings.urls')),
    path('exams/', include('exams.urls')),
    path('reports/', reports, name='reports'),
    path('settings/', settings_view, name='settings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

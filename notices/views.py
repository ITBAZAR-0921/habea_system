from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from config.permissions import MANAGER_ROLES, role_required
from employees.models import Employee

from .forms import NoticeForm
from .models import Notice, NoticeRead
from .services import get_applicable_notices_for_employee, get_or_create_notice_read


@role_required(MANAGER_ROLES)
def notice_list(request):
    notices = Notice.objects.select_related('created_by').all()
    return render(request, 'notices/notice_list.html', {'notices': notices})


@role_required(MANAGER_ROLES)
def notice_create(request):
    form = NoticeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        notice = form.save(commit=False)
        notice.created_by = request.user
        notice.save()
        form.save_m2m()
        messages.success(request, 'Мэдэгдэл амжилттай үүслээ.')
        return redirect('notice_list')

    return render(request, 'notices/notice_form.html', {'form': form, 'is_edit': False})


@role_required(MANAGER_ROLES)
def notice_update(request, notice_id):
    notice = get_object_or_404(Notice, pk=notice_id)
    form = NoticeForm(request.POST or None, instance=notice)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Мэдэгдэл амжилттай шинэчлэгдлээ.')
        return redirect('notice_list')

    return render(request, 'notices/notice_form.html', {'form': form, 'is_edit': True, 'notice': notice})


@role_required(MANAGER_ROLES)
def notice_delete(request, notice_id):
    notice = get_object_or_404(Notice, pk=notice_id)
    if request.method == 'POST':
        notice.delete()
        messages.success(request, 'Мэдэгдэл устгагдлаа.')
        return redirect('notice_list')

    return render(request, 'notices/notice_delete_confirm.html', {'notice': notice})


@login_required
def my_notices(request):
    employee = Employee.objects.filter(user=request.user).first()
    if employee is None:
        return render(request, 'notices/my_notices.html', {'notice_items': []})
    notices = get_applicable_notices_for_employee(employee)
    reads = NoticeRead.objects.filter(employee=employee).select_related('notice')
    read_map = {item.notice_id: item for item in reads}

    items = []
    newly_read = []
    for notice in notices:
        read_obj = read_map.get(notice.id)
        if read_obj is None:
            newly_read.append(NoticeRead(employee=employee, notice=notice))
        items.append(
            {
                'notice': notice,
                'read': read_obj,
                'is_unread': read_obj is None,
                'is_acknowledged': bool(read_obj and read_obj.acknowledged),
            }
        )

    if newly_read:
        NoticeRead.objects.bulk_create(newly_read, ignore_conflicts=True)

    return render(request, 'notices/my_notices.html', {'notice_items': items})


@login_required
def acknowledge_notice(request, notice_id):
    if request.method != 'POST':
        return redirect('my_notices')

    employee = get_object_or_404(Employee, user=request.user)
    notice = get_object_or_404(get_applicable_notices_for_employee(employee), pk=notice_id)

    if notice.requires_acknowledgement:
        read_obj, _ = get_or_create_notice_read(employee, notice)
        read_obj.acknowledged = True
        read_obj.save()
        messages.success(request, 'Мэдэгдэлтэй танилцсан тэмдэглэл хадгалагдлаа.')

    return redirect('my_notices')

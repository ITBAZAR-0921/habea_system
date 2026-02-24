from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from config.permissions import MANAGER_ROLES, get_user_role, role_required
from employees.models import Employee

from .forms import ParticipationStatusForm, TrainingForm, TrainingMaterialFormSet
from .models import Training, TrainingParticipation
from .services import sync_training_participations


def _manager_training_queryset():
    return Training.objects.select_related('created_by').prefetch_related('materials', 'participations')


@role_required(MANAGER_ROLES)
def training_list(request):
    trainings = _manager_training_queryset().all()
    return render(request, 'trainings/training_list.html', {'trainings': trainings})


@role_required(MANAGER_ROLES)
def training_create(request):
    form = TrainingForm(request.POST or None)
    formset = TrainingMaterialFormSet(request.POST or None, request.FILES or None, prefix='materials')
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        training = form.save(commit=False)
        training.created_by = request.user
        training.save()
        form.save_m2m()
        formset.instance = training
        formset.save()
        result = sync_training_participations(training)
        messages.success(request, f"Сургалт үүслээ. {result['created']} ажилтанд хуваариллаа.")
        return redirect('training_detail', training_id=training.id)

    return render(
        request,
        'trainings/training_form.html',
        {'form': form, 'formset': formset, 'is_edit': False},
    )


@role_required(MANAGER_ROLES)
def training_update(request, training_id):
    training = get_object_or_404(Training, pk=training_id)
    form = TrainingForm(request.POST or None, instance=training)
    formset = TrainingMaterialFormSet(
        request.POST or None,
        request.FILES or None,
        instance=training,
        prefix='materials',
    )
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        result = sync_training_participations(training)
        messages.success(request, f"Сургалт шинэчлэгдлээ. Нэмэлт {result['created']} хуваарилалт үүсгэлээ.")
        return redirect('training_detail', training_id=training.id)

    return render(
        request,
        'trainings/training_form.html',
        {'form': form, 'formset': formset, 'is_edit': True, 'training': training},
    )


@role_required(MANAGER_ROLES)
def training_delete(request, training_id):
    training = get_object_or_404(Training, pk=training_id)
    if request.method == 'POST':
        training.delete()
        messages.success(request, 'Сургалт устгагдлаа.')
        return redirect('training_list')

    return render(request, 'trainings/training_delete_confirm.html', {'training': training})


@login_required
def training_detail(request, training_id):
    role = get_user_role(request.user)

    if role in MANAGER_ROLES:
        training = get_object_or_404(
            _manager_training_queryset(),
            pk=training_id,
        )
        participations = training.participations.select_related('employee')

        return render(
            request,
            'trainings/training_detail.html',
            {
                'training': training,
                'participations': participations,
                'is_manager': True,
            },
        )

    employee = get_object_or_404(Employee, user=request.user)
    participation = get_object_or_404(
        TrainingParticipation.objects.select_related('training').prefetch_related('training__materials'),
        training_id=training_id,
        employee=employee,
    )

    status_form = ParticipationStatusForm(request.POST or None, instance=participation)
    if request.method == 'POST' and 'update_status' in request.POST:
        if status_form.is_valid():
            status_form.save()
            messages.success(request, 'Сургалтын төлөв шинэчлэгдлээ.')
            return redirect('training_detail', training_id=training_id)

    return render(
        request,
        'trainings/training_detail.html',
        {
            'training': participation.training,
            'participation': participation,
            'status_form': status_form,
            'is_manager': False,
        },
    )


@login_required
def my_trainings(request):
    employee = Employee.objects.filter(user=request.user).first()
    if employee is None:
        return render(request, 'trainings/my_trainings.html', {'participations': []})

    participations = (
        TrainingParticipation.objects.select_related('training')
        .filter(employee=employee, training__is_active=True)
        .order_by('-training__start_date')
    )
    return render(request, 'trainings/my_trainings.html', {'participations': participations})

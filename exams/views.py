from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView

from config.permissions import get_user_role
from employees.models import Employee

from .forms import ExamForm, QuestionChoiceForm, QuestionFormSet
from .models import Exam, ExamAttempt, Question


def _employee_available_exams(employee):
    if employee is None:
        return Exam.objects.none()

    department_ids = []
    current = employee.department
    while current is not None:
        department_ids.append(current.id)
        current = current.parent

    queryset = Exam.objects.filter(is_active=True)
    filters = models.Q(target_type=Exam.TargetType.ORGANIZATION_WIDE)
    if department_ids:
        filters |= models.Q(target_type=Exam.TargetType.DEPARTMENT, departments__id__in=department_ids)
    if employee.position_id:
        filters |= models.Q(target_type=Exam.TargetType.POSITION, positions__id=employee.position_id)
    return queryset.filter(filters).distinct()


def _validate_exam_questions(exam):
    for question in exam.questions.all():
        choices = list(question.choices.all())
        if len(choices) < 2:
            return False
        if sum(1 for choice in choices if choice.is_correct) != 1:
            return False
    return True


class ExamManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = {'system_admin', 'hse_manager', 'department_head'}

    def test_func(self):
        return get_user_role(self.request.user) in self.allowed_roles


class EmployeeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return get_user_role(self.request.user) == 'employee'


class OfficialAttemptMixin(EmployeeRequiredMixin):
    attempt = None

    def get_employee(self):
        return get_object_or_404(Employee, user=self.request.user)

    def get_attempt(self):
        if self.attempt is None:
            self.attempt = get_object_or_404(
                ExamAttempt.objects.select_related('exam', 'employee'),
                pk=self.kwargs['attempt_id'],
                employee=self.get_employee(),
            )
        return self.attempt


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'

    def get_queryset(self):
        role = get_user_role(self.request.user)
        if role in {'system_admin', 'hse_manager', 'department_head'}:
            return Exam.objects.all()
        employee = Employee.objects.filter(user=self.request.user).first()
        return _employee_available_exams(employee)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = get_user_role(self.request.user)
        context['is_manager'] = role in {'system_admin', 'hse_manager', 'department_head'}
        context['is_employee'] = role == 'employee'
        return context


class ExamCreateView(ExamManagerRequiredMixin, FormView):
    template_name = 'exams/exam_form.html'
    form_class = ExamForm

    def form_valid(self, form):
        exam = form.save(commit=False)
        exam.created_by = self.request.user
        exam.save()
        form.save_m2m()
        messages.success(self.request, 'Шалгалт хадгалагдлаа. Одоо асуултуудаа нэмнэ үү.')
        return redirect('exam_questions_manage', exam_id=exam.id)


class ExamUpdateView(ExamManagerRequiredMixin, FormView):
    template_name = 'exams/exam_form.html'
    form_class = ExamForm

    def get_exam(self):
        return get_object_or_404(Exam, pk=self.kwargs['exam_id'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_exam()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['exam'] = self.get_exam()
        return context

    def form_valid(self, form):
        exam = form.save()
        messages.success(self.request, 'Шалгалт шинэчлэгдлээ.')
        return redirect('exam_questions_manage', exam_id=exam.id)


class ExamDeleteView(ExamManagerRequiredMixin, View):
    template_name = 'exams/exam_delete_confirm.html'

    def get_exam(self):
        return get_object_or_404(Exam, pk=self.kwargs['exam_id'])

    def get(self, request, exam_id):
        exam = self.get_exam()
        return render(request, self.template_name, {'exam': exam})

    def post(self, request, exam_id):
        exam = self.get_exam()
        if exam.exam_type == Exam.ExamType.OFFICIAL and exam.attempts.exists():
            exam.is_active = False
            exam.save(update_fields=['is_active'])
            messages.warning(request, 'Албан ёсны шалгалт тайлантай тул идэвхгүй болголоо.')
        else:
            exam.delete()
            messages.success(request, 'Шалгалт устгагдлаа.')
        return redirect('exam_list')


class ExamQuestionManageView(ExamManagerRequiredMixin, View):
    template_name = 'exams/exam_questions_manage.html'

    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        formset = QuestionFormSet(instance=exam, prefix='questions')
        return render(request, self.template_name, {'exam': exam, 'formset': formset})

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        formset = QuestionFormSet(request.POST, request.FILES, instance=exam, prefix='questions')
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Асуултууд амжилттай хадгалагдлаа.')
            return redirect('exam_list')
        return render(request, self.template_name, {'exam': exam, 'formset': formset})


class ExamStartView(EmployeeRequiredMixin, View):
    def post(self, request, exam_id):
        employee = get_object_or_404(Employee, user=request.user)
        exam = get_object_or_404(_employee_available_exams(employee), pk=exam_id)
        if not exam.questions.exists():
            messages.error(request, 'Энэ шалгалтад асуулт бүртгэгдээгүй байна.')
            return redirect('exam_list')
        if not _validate_exam_questions(exam):
            messages.error(request, 'Шалгалтын асуулт/choice бүтэц буруу байна (2+ choice, 1 зөв).')
            return redirect('exam_list')

        if exam.exam_type == Exam.ExamType.OFFICIAL:
            if ExamAttempt.objects.filter(exam=exam, employee=employee).exists():
                messages.warning(request, 'Та энэ шалгалтыг аль хэдийн өгсөн байна.')
                return redirect('exam_list')
            attempt = ExamAttempt.objects.create(exam=exam, employee=employee)
            return redirect('attempt_question', attempt_id=attempt.id, number=1)

        token = int(timezone.now().timestamp())
        request.session[f'practice_exam_{token}'] = {
            'exam_id': exam.id,
            'started_at': timezone.now().isoformat(),
            'answers': {},
            'user_id': request.user.id,
        }
        request.session.modified = True
        return redirect('attempt_question', attempt_id=token, number=1)


class AttemptQuestionView(EmployeeRequiredMixin, FormView):
    template_name = 'exams/exam_question.html'
    form_class = QuestionChoiceForm

    exam = None
    question = None
    is_official = False

    def _get_practice_data(self):
        return self.request.session.get(f'practice_exam_{self.kwargs["attempt_id"]}')

    def _load_context(self):
        attempt_id = self.kwargs['attempt_id']
        employee = get_object_or_404(Employee, user=self.request.user)

        attempt = ExamAttempt.objects.filter(pk=attempt_id, employee=employee).select_related('exam').first()
        if attempt:
            self.is_official = True
            self.exam = attempt.exam
            return attempt, None

        practice = self._get_practice_data()
        if not practice or practice.get('user_id') != self.request.user.id:
            raise Http404('Attempt not found')

        self.exam = get_object_or_404(Exam, pk=practice['exam_id'], is_active=True)
        return None, practice

    def dispatch(self, request, *args, **kwargs):
        attempt, practice = self._load_context()

        questions = list(self.exam.questions.prefetch_related('choices').all())
        number = int(kwargs['number'])
        if number < 1 or number > len(questions):
            return redirect('attempt_finish', attempt_id=kwargs['attempt_id'])
        self.question = questions[number - 1]

        started_at = attempt.started_at if attempt else timezone.datetime.fromisoformat(practice['started_at'])
        expires_at = started_at + timedelta(minutes=self.exam.duration_minutes)
        if timezone.now() >= expires_at:
            return redirect('attempt_finish', attempt_id=kwargs['attempt_id'])

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['question'] = self.question
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        attempt_id = self.kwargs['attempt_id']

        if self.is_official:
            employee = get_object_or_404(Employee, user=self.request.user)
            attempt = get_object_or_404(ExamAttempt, pk=attempt_id, employee=employee)
            response = attempt.responses.filter(question=self.question).first()
            if response:
                initial['choice'] = response.selected_choice_id
        else:
            practice = self._get_practice_data()
            if practice:
                selected = practice['answers'].get(str(self.question.id))
                if selected:
                    initial['choice'] = selected

        return initial

    def form_valid(self, form):
        attempt_id = self.kwargs['attempt_id']
        next_number = int(self.kwargs['number']) + 1
        total_questions = self.exam.questions.count()

        if self.is_official:
            employee = get_object_or_404(Employee, user=self.request.user)
            attempt = get_object_or_404(ExamAttempt, pk=attempt_id, employee=employee)
            form.save_official(attempt)
        else:
            practice = self._get_practice_data()
            if not practice:
                raise Http404('Practice attempt not found')
            practice['answers'][str(self.question.id)] = form.cleaned_data['choice'].id
            self.request.session[f'practice_exam_{attempt_id}'] = practice
            self.request.session.modified = True

        if next_number > total_questions:
            return redirect('attempt_finish', attempt_id=attempt_id)
        return redirect('attempt_question', attempt_id=attempt_id, number=next_number)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_questions = self.exam.questions.count()
        current_number = int(self.kwargs['number'])

        if self.is_official:
            employee = get_object_or_404(Employee, user=self.request.user)
            attempt = get_object_or_404(ExamAttempt, pk=self.kwargs['attempt_id'], employee=employee)
            started_at = attempt.started_at
        else:
            practice = self._get_practice_data()
            started_at = timezone.datetime.fromisoformat(practice['started_at'])
            attempt = None

        expires_at = started_at + timedelta(minutes=self.exam.duration_minutes)
        remaining_seconds = max(0, int((expires_at - timezone.now()).total_seconds()))

        context.update(
            {
                'exam': self.exam,
                'attempt': attempt,
                'attempt_id': self.kwargs['attempt_id'],
                'question': self.question,
                'current_number': current_number,
                'total_questions': total_questions,
                'remaining_seconds': remaining_seconds,
                'prev_number': current_number - 1 if current_number > 1 else None,
            }
        )
        return context


class AttemptFinishView(EmployeeRequiredMixin, View):
    def get(self, request, attempt_id):
        employee = get_object_or_404(Employee, user=request.user)
        attempt = ExamAttempt.objects.filter(pk=attempt_id, employee=employee).select_related('exam').first()

        if attempt:
            if attempt.completed_at is None:
                attempt.finish()
            messages.success(request, 'Албан ёсны шалгалт дууслаа.')
            return redirect('exam_result', attempt_id=attempt.id)

        practice = request.session.get(f'practice_exam_{attempt_id}')
        if not practice or practice.get('user_id') != request.user.id:
            raise Http404('Attempt not found')

        exam = get_object_or_404(Exam, pk=practice['exam_id'])
        answers = practice.get('answers', {})
        score = 0
        for question in exam.questions.all():
            selected_id = answers.get(str(question.id))
            if selected_id and question.choices.filter(pk=selected_id, is_correct=True).exists():
                score += question.score

        result = {
            'exam_title': exam.title,
            'score': score,
            'pass_score': exam.pass_score,
            'is_passed': score >= exam.pass_score,
            'is_practice': True,
        }
        request.session[f'practice_result_{attempt_id}'] = result
        request.session.pop(f'practice_exam_{attempt_id}', None)
        request.session.modified = True
        return redirect('exam_result', attempt_id=attempt_id)


class ExamResultView(EmployeeRequiredMixin, DetailView):
    model = ExamAttempt
    pk_url_kwarg = 'attempt_id'
    template_name = 'exams/exam_result.html'
    context_object_name = 'attempt'

    def get_queryset(self):
        employee = get_object_or_404(Employee, user=self.request.user)
        return ExamAttempt.objects.select_related('exam').filter(employee=employee)

    def get(self, request, *args, **kwargs):
        result = request.session.get(f'practice_result_{kwargs["attempt_id"]}')
        if result:
            response = render(request, self.template_name, {'practice_result': result})
            request.session.pop(f'practice_result_{kwargs["attempt_id"]}', None)
            request.session.modified = True
            return response
        return super().get(request, *args, **kwargs)

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from employees.models import Department, Employee, Position

from .models import Choice, Exam, ExamAttempt, Question


class ExamFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='emp', password='pass1234')
        group, _ = Group.objects.get_or_create(name='employee')
        self.user.groups.add(group)

        dept = Department.objects.create(name='Test Dept')
        position = Position.objects.create(name='Worker')
        self.employee = Employee.objects.create(
            user=self.user,
            first_name='E',
            last_name='M',
            register='AA55555555',
            department=dept,
            position=position,
        )

        self.exam = Exam.objects.create(
            title='Safety Exam',
            exam_type=Exam.ExamType.OFFICIAL,
            target_type=Exam.TargetType.ORGANIZATION_WIDE,
            duration_minutes=10,
            pass_score=1,
            is_active=True,
            created_by=self.user,
        )
        q1 = Question.objects.create(exam=self.exam, text='Q1', order=1, score=1)
        q2 = Question.objects.create(exam=self.exam, text='Q2', order=2, score=1)
        self.c1 = Choice.objects.create(question=q1, text='A', is_correct=True)
        Choice.objects.create(question=q1, text='B', is_correct=False)
        self.c2 = Choice.objects.create(question=q2, text='C', is_correct=False)
        Choice.objects.create(question=q2, text='D', is_correct=True)

    def test_official_exam_finish_and_score(self):
        self.client.login(username='emp', password='pass1234')
        start = self.client.post(reverse('exam_start', kwargs={'exam_id': self.exam.id}))
        self.assertEqual(start.status_code, 302)

        attempt = ExamAttempt.objects.get(employee=self.employee, exam=self.exam)
        self.client.post(
            reverse('attempt_question', kwargs={'attempt_id': attempt.id, 'number': 1}),
            data={'choice': self.c1.id},
        )
        self.client.post(
            reverse('attempt_question', kwargs={'attempt_id': attempt.id, 'number': 2}),
            data={'choice': self.c2.id},
        )
        self.client.get(reverse('attempt_finish', kwargs={'attempt_id': attempt.id}))

        attempt.refresh_from_db()
        self.assertIsNotNone(attempt.completed_at)
        self.assertEqual(attempt.total_score, 1)
        self.assertTrue(attempt.is_passed)

    def test_employee_cannot_access_others_attempt(self):
        other_user = User.objects.create_user(username='other', password='pass1234')
        other_group, _ = Group.objects.get_or_create(name='employee')
        other_user.groups.add(other_group)
        dept = Department.objects.create(name='Another Dept')
        pos = Position.objects.create(name='Another Position')
        other_emp = Employee.objects.create(
            user=other_user,
            first_name='O',
            last_name='T',
            register='AA66666666',
            department=dept,
            position=pos,
        )
        attempt = ExamAttempt.objects.create(exam=self.exam, employee=other_emp)

        self.client.login(username='emp', password='pass1234')
        response = self.client.get(reverse('attempt_question', kwargs={'attempt_id': attempt.id, 'number': 1}))
        self.assertEqual(response.status_code, 404)

    def test_inactive_exam_cannot_start(self):
        self.exam.is_active = False
        self.exam.save(update_fields=['is_active'])
        self.client.login(username='emp', password='pass1234')
        response = self.client.post(reverse('exam_start', kwargs={'exam_id': self.exam.id}))
        self.assertEqual(response.status_code, 404)

    def test_practice_exam_not_saved_to_attempt_table(self):
        practice = Exam.objects.create(
            title='Practice Test',
            exam_type=Exam.ExamType.PRACTICE,
            target_type=Exam.TargetType.ORGANIZATION_WIDE,
            duration_minutes=10,
            pass_score=1,
            is_active=True,
            created_by=self.user,
        )
        q = Question.objects.create(exam=practice, text='PQ1', order=1, score=1)
        c = Choice.objects.create(question=q, text='X', is_correct=True)
        Choice.objects.create(question=q, text='Y', is_correct=False)

        self.client.login(username='emp', password='pass1234')
        start = self.client.post(reverse('exam_start', kwargs={'exam_id': practice.id}))
        self.assertEqual(start.status_code, 302)
        self.assertEqual(ExamAttempt.objects.filter(exam=practice).count(), 0)

        location = start['Location']
        self.client.post(location, data={'choice': c.id})
        finish_url = location.replace('/question/1/', '/finish/')
        finish_response = self.client.get(finish_url)
        self.assertEqual(finish_response.status_code, 302)
        result_url = finish_response['Location']
        result_response = self.client.get(result_url)
        self.assertContains(result_response, 'Жишиг тест')
        self.assertEqual(ExamAttempt.objects.filter(exam=practice).count(), 0)

    def test_official_exam_second_attempt_blocked(self):
        self.client.login(username='emp', password='pass1234')
        self.client.post(reverse('exam_start', kwargs={'exam_id': self.exam.id}))
        self.client.post(reverse('exam_start', kwargs={'exam_id': self.exam.id}), follow=True)
        self.assertEqual(ExamAttempt.objects.filter(employee=self.employee, exam=self.exam).count(), 1)


class ExamDeleteLogicTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='mgr', password='pass1234')
        group, _ = Group.objects.get_or_create(name='hse_manager')
        self.manager.groups.add(group)

        emp_user = User.objects.create_user(username='emp3', password='pass1234')
        emp_group, _ = Group.objects.get_or_create(name='employee')
        emp_user.groups.add(emp_group)
        dept = Department.objects.create(name='Delete Dept')
        pos = Position.objects.create(name='Delete Pos')
        self.employee = Employee.objects.create(
            user=emp_user,
            first_name='X',
            last_name='Y',
            register='AA77777777',
            department=dept,
            position=pos,
        )

    def test_official_delete_deactivates_if_attempt_exists(self):
        exam = Exam.objects.create(
            title='Official Delete',
            exam_type=Exam.ExamType.OFFICIAL,
            target_type=Exam.TargetType.ORGANIZATION_WIDE,
            duration_minutes=10,
            pass_score=1,
            is_active=True,
            created_by=self.manager,
        )
        ExamAttempt.objects.create(exam=exam, employee=self.employee)

        self.client.login(username='mgr', password='pass1234')
        response = self.client.post(reverse('exam_delete', kwargs={'exam_id': exam.id}))
        self.assertEqual(response.status_code, 302)
        exam.refresh_from_db()
        self.assertFalse(exam.is_active)

    def test_practice_delete_removes_exam(self):
        exam = Exam.objects.create(
            title='Practice Delete',
            exam_type=Exam.ExamType.PRACTICE,
            target_type=Exam.TargetType.ORGANIZATION_WIDE,
            duration_minutes=10,
            pass_score=1,
            is_active=True,
            created_by=self.manager,
        )
        self.client.login(username='mgr', password='pass1234')
        response = self.client.post(reverse('exam_delete', kwargs={'exam_id': exam.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Exam.objects.filter(id=exam.id).exists())

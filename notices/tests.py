from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from employees.models import Department, Employee, Position

from .models import Notice
from .services import get_applicable_notices_for_employee


class NoticeTargetingTests(TestCase):
    def setUp(self):
        self.parent_dept = Department.objects.create(name='Техникийн хэлтэс')
        self.child_dept = Department.objects.create(name='Шугам сүлжээ', parent=self.parent_dept)
        self.position = Position.objects.create(name='Инженер')

        user = User.objects.create_user(username='emp', password='pass1234')
        self.employee = Employee.objects.create(
            user=user,
            first_name='A',
            last_name='B',
            register='AA11111111',
            department=self.child_dept,
            position=self.position,
        )

    def test_department_notice_visible_to_child_department_employee(self):
        notice = Notice.objects.create(
            title='Хэлтсийн мэдэгдэл',
            content='Текст',
            notice_type=Notice.NoticeType.DEPARTMENT,
            created_by=self.employee.user,
            is_active=True,
        )
        notice.departments.add(self.parent_dept)

        notices = get_applicable_notices_for_employee(self.employee)
        self.assertIn(notice, notices)


class NoticePermissionTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='emp2', password='pass1234')
        position = Position.objects.create(name='Мэргэжилтэн')
        dept = Department.objects.create(name='Үйлдвэрлэл')
        self.employee = Employee.objects.create(
            user=user,
            first_name='C',
            last_name='D',
            register='AA22222222',
            department=dept,
            position=position,
        )
        group, _ = Group.objects.get_or_create(name='employee')
        user.groups.add(group)

    def test_employee_cannot_open_notice_management(self):
        self.client.login(username='emp2', password='pass1234')
        response = self.client.get(reverse('notice_list'))
        self.assertEqual(response.status_code, 403)

    def test_employee_can_open_my_notices(self):
        self.client.login(username='emp2', password='pass1234')
        response = self.client.get(reverse('my_notices'))
        self.assertEqual(response.status_code, 200)

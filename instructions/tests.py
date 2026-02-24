from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from employees.models import Employee, Position
from .models import Instruction, InstructionRecord


class InstructionRecordStatusTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='emp1', password='pass1234')
        position = Position.objects.create(name='Engineer')
        self.employee = Employee.objects.create(
            user=user,
            first_name='Test',
            last_name='Employee',
            register='AA12345678',
            position=position,
            hired_date=timezone.localdate(),
        )
        self.instruction = Instruction.objects.create(
            title='Галын аюулгүй ажиллагаа',
            description='Туршилтын заавар',
            instruction_type=Instruction.InstructionType.ORGANIZATION,
            validity_days=365,
        )

    def test_next_due_date_is_calculated(self):
        completed = timezone.localdate() - timedelta(days=10)
        record = InstructionRecord.objects.create(
            employee=self.employee,
            instruction=self.instruction,
            completed_date=completed,
        )
        self.assertEqual(record.next_due_date, completed + timedelta(days=365))

    def test_acknowledged_sets_date(self):
        record = InstructionRecord.objects.create(
            employee=self.employee,
            instruction=self.instruction,
        )
        record.acknowledged = True
        record.save()
        self.assertIsNotNone(record.acknowledged_date)


class InstructionViewsAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='staff', password='pass1234')
        group, _ = Group.objects.get_or_create(name='employee')
        self.user.groups.add(group)

    def test_instruction_list_forbidden_for_employee_role(self):
        self.client.login(username='staff', password='pass1234')
        response = self.client.get(reverse('instruction_list'))
        self.assertEqual(response.status_code, 403)

    def test_my_instructions_requires_login(self):
        response = self.client.get(reverse('my_instruction_records'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

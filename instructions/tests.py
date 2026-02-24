from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from employees.models import Employee
from .models import Instruction, InstructionRecord


class InstructionRecordStatusTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='emp1', password='pass1234')
        self.employee = Employee.objects.create(
            user=user,
            first_name='Test',
            last_name='Employee',
            register='AA12345678',
            position='Engineer',
            hired_date=timezone.localdate(),
        )
        self.instruction = Instruction.objects.create(
            title='Галын аюулгүй ажиллагаа',
            description='Туршилтын заавар',
            validity_days=365,
        )

    def test_status_overdue(self):
        record = InstructionRecord.objects.create(
            employee=self.employee,
            instruction=self.instruction,
            completed_on=timezone.localdate() - timedelta(days=400),
            valid_until=timezone.localdate() - timedelta(days=1),
        )
        self.assertEqual(record.status, InstructionRecord.Status.OVERDUE)

    def test_status_due_soon(self):
        record = InstructionRecord.objects.create(
            employee=self.employee,
            instruction=self.instruction,
            completed_on=timezone.localdate() - timedelta(days=300),
            valid_until=timezone.localdate() + timedelta(days=10),
        )
        self.assertEqual(record.status, InstructionRecord.Status.DUE_SOON)


class InstructionViewsAuthTests(TestCase):
    def test_instruction_list_requires_login(self):
        response = self.client.get(reverse('instruction_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

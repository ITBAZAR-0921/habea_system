from datetime import date

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from employees.models import Department, Employee, Position

from .models import Training, TrainingMaterial, TrainingParticipation
from .services import sync_training_participations


class TrainingParticipationTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name='Техникийн хэлтэс')
        self.position = Position.objects.create(name='Инженер')

        user = User.objects.create_user(username='emp1', password='pass1234')
        self.employee = Employee.objects.create(
            user=user,
            first_name='A',
            last_name='B',
            register='AA33333333',
            department=self.department,
            position=self.position,
        )

        self.training = Training.objects.create(
            title='Аюулгүй ажиллагаа',
            description='Туршилтын сургалт',
            training_type=Training.TrainingType.DEPARTMENT,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            trainer_name='Багш',
            required=True,
            created_by=user,
        )
        self.training.departments.add(self.department)

    def test_sync_creates_participation(self):
        result = sync_training_participations(self.training)
        self.assertEqual(result['created'], 1)
        self.assertTrue(
            TrainingParticipation.objects.filter(training=self.training, employee=self.employee).exists()
        )


class TrainingMaterialValidationTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='mgr', password='pass1234')
        self.training = Training.objects.create(
            title='Материалтай сургалт',
            training_type=Training.TrainingType.ORGANIZATION_WIDE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 5),
            trainer_name='Сургагч',
            created_by=user,
        )

    def test_text_material_requires_text_content(self):
        material = TrainingMaterial(
            training=self.training,
            title='Текст материал',
            material_type=TrainingMaterial.MaterialType.TEXT,
            text_content='',
        )
        with self.assertRaises(ValidationError):
            material.full_clean()

    def test_image_material_disallows_text_content(self):
        material = TrainingMaterial(
            training=self.training,
            title='Image материал',
            material_type=TrainingMaterial.MaterialType.IMAGE,
            text_content='илүүдэл текст',
            file=SimpleUploadedFile('test.jpg', b'image-bytes', content_type='image/jpeg'),
        )
        with self.assertRaises(ValidationError):
            material.full_clean()

    def test_text_material_disallows_file(self):
        material = TrainingMaterial(
            training=self.training,
            title='Text+file',
            material_type=TrainingMaterial.MaterialType.TEXT,
            text_content='текст',
            file=SimpleUploadedFile('file.pdf', b'pdf-bytes', content_type='application/pdf'),
        )
        with self.assertRaises(ValidationError):
            material.full_clean()


class EmployeeTrainingViewTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='emp2', password='pass1234')
        group, _ = Group.objects.get_or_create(name='employee')
        user.groups.add(group)

        dept = Department.objects.create(name='Үйлдвэрлэл')
        position = Position.objects.create(name='Мэргэжилтэн')
        employee = Employee.objects.create(
            user=user,
            first_name='C',
            last_name='D',
            register='AA44444444',
            department=dept,
            position=position,
        )

        self.training = Training.objects.create(
            title='Ажилтны сургалт',
            training_type=Training.TrainingType.SPECIFIC_EMPLOYEE,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
            trainer_name='Сургагч',
            created_by=user,
        )
        self.training.employees.add(employee)
        sync_training_participations(self.training)

    def test_employee_can_update_status(self):
        self.client.login(username='emp2', password='pass1234')
        response = self.client.post(
            reverse('training_detail', kwargs={'training_id': self.training.id}),
            data={'status': TrainingParticipation.Status.COMPLETED, 'update_status': '1'},
        )
        self.assertEqual(response.status_code, 302)
        participation = TrainingParticipation.objects.get(training=self.training)
        self.assertEqual(participation.status, TrainingParticipation.Status.COMPLETED)
        self.assertIsNotNone(participation.completed_at)

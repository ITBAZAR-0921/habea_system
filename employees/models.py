from django.db import models

# Create your models here.
class Employee(models.Model):
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	register = models.CharField(max_length=20, unique=True)

	position = models.CharField(max_length=150)
	department = models.CharField(max_length=150)

	phone = models.CharField(max_length=20, blank=True)
	email =  models.EmailField(blank=True)

	photo = models.ImageField(upload_to="employees/", blank=True)

	hired_date = models.DateField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.last_name} {self.first_name}"

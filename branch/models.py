from django.db import models
from user.models import Teacher
from student.models import Student

class Branch(models.Model):
    name = models.CharField(max_length=50, verbose_name="지점 이름")
    location = models.CharField(max_length=100, verbose_name="지점 위치")
    teachers = models.ManyToManyField(Teacher, verbose_name="선생님들")
    students = models.ManyToManyField(Student, verbose_name="학생들")
    manager = models.OneToOneField(Teacher, on_delete=models.SET_NULL, null=True, verbose_name="지점 최고관리자")

    def __str__(self):
        return self.name

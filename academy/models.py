from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from datetime import datetime
from user.models import User

class Branch(models.Model):
    name = models.CharField(verbose_name="지점", max_length=50)

    def __str__(self):
        return self.name
    
class Academy(models.Model):
    name = models.CharField(verbose_name="학원 이름", max_length=100)
    location = models.CharField(verbose_name="위치", max_length=200)
    teachers = models.ForeignKey(
        to='user.User',
        verbose_name="매니저",
        related_name='teacher_academies',
        on_delete=models.SET_NULL,
        null=True
    )
    students = models.ManyToManyField(User,verbose_name='학생들')
    manager = models.OneToOneField(
        to='user.User',
        verbose_name="헤드매니저",
        related_name='managed_academy',
        on_delete=models.SET_NULL,
        null=True
    )
    branch = models.ForeignKey(
        to=Branch,
        verbose_name="지점",
        related_name='academies',
        on_delete=models.SET_NULL,
        null=True
    )

    def __str__(self):
        return self.name
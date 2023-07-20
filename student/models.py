from django.db import models
from user.abstract_models import AbstractUserProfile
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from datetime import datetime
from branch.models import Branch


class StudentProfile(AbstractUserProfile):
    # 추가적인 필드들 정의
    pmobileno = models.CharField(verbose_name="부모님 연락처", max_length=20)
    origin = models.CharField(verbose_name="원번", max_length=20)

    def __str__(self):
        return self.user.username

# class Student(models.Model):
    # 추가적인 필드들 정의 (예: 성적 데이터 등)
    # 이 모델에서는 추상 모델인 AbstractUserProfile을 상속받지 않습니다.
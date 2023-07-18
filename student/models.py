from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from datetime import datetime
from branch.models import Branch

class StudentManager(BaseUserManager):
    def create_stuent(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        
        student = self.model(username=username, **extra_fields)
        student.set_password(password)
        student.save(using=self._db)
        return student

class Student(AbstractBaseUser):
    class Meta:
        db_table = "student"

    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(verbose_name="사용자 이메일", max_length=254, blank=True)
    branches = models.ManyToManyField(Branch, verbose_name="소속 지점들")

    REQUIRED_FIELDS = []

    objects = StudentManager()

    USERNAME_FIELD = 'studentname'

    def __str__(self):
        return self.username

class StudentProfile(models.Model):
    class Meta:
        db_table = "student_profile"
    student = models.OneToOneField(to=Student, verbose_name="사용자", on_delete=models.CASCADE)
    kor_name = models.CharField("한국이름", max_length=20, default='퍼플')
    eng_name = models.CharField("영어이름", max_length=20, default='purple')
    origin = models.CharField("원번", max_length=10, default='P0000')
    GENDERS = (
        ('M', '남성(Man)'),
        ('W', '여성(Woman)'),
    )
    gender = models.CharField(verbose_name="성별", max_length=1, choices=GENDERS)
    mobileno = models.CharField(verbose_name="연락처", max_length=20, unique=True)
    pmobileno = models.CharField(verbose_name="학부모연락처", max_length=20, unique=True)
    register_date = models.DateTimeField(verbose_name="가입일", auto_now_add=True)
    birth_year = models.PositiveIntegerField(verbose_name="출생 연도", null=True, blank=True)

    @property
    def age(self):
        if self.birth_year:
            current_year = datetime.now().year
            return current_year - self.user.birth_year
        return None

from django.db import models
from .abstract_models import AbstractUserProfile
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from datetime import datetime
from branch.models import Branch

class UserCategory(models.Model):
    name = models.CharField(verbose_name="카테고리 이름", max_length=50)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, AbstractUserProfile):
    class Meta:
        db_table = "user"

    username = models.CharField("사용자계정",max_length=50, unique=True)
    email = models.EmailField(verbose_name="사용자 이메일", max_length=254, blank=True)
    password = models.CharField("비밀번호",max_length=128)
    user_category = models.ForeignKey(UserCategory, verbose_name="카테고리", on_delete=models.SET_NULL, null=True)
    branches = models.ManyToManyField(Branch, verbose_name="소속 지점들")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    REQUIRED_FIELDS = []

    objects = UserManager()

    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username

    # admin 권한 설정
    @property
    def is_staff(self):
        return self.is_staff

class UserProfile(AbstractUserProfile):

    def __str__(self):
        return self.user.username

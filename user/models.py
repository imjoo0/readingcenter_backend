from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from datetime import datetime
# from branch.models import Branch
# user가 학생일 경우에만 몇가지 프로필 사항을 추가하도록 하기 위한 모듈 
from model_utils import FieldTracker
from django.db.models.signals import pre_save
from django.dispatch import receiver

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


class User(AbstractBaseUser):
    class Meta:
        db_table = "user"

    username = models.CharField("사용자계정",max_length=50, unique=True)
    email = models.EmailField(verbose_name="사용자 이메일", max_length=254, blank=True)
    password = models.CharField("비밀번호",max_length=128)
    user_category = models.ForeignKey(UserCategory, verbose_name="카테고리", on_delete=models.SET_NULL, null=True)
    # branches = models.ManyToManyField(Branch, verbose_name="소속 지점들")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  
    
    REQUIRED_FIELDS = []

    objects = UserManager()

    USERNAME_FIELD = 'username'

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def __str__(self):
        return self.username
    
@receiver(pre_save, sender=User)
def add_user_profile_fields(sender, instance, **kwargs):
    try:
        user_profile = instance.userprofile
    except UserProfile.DoesNotExist:
        user_category = instance.user_category
        if user_category and user_category.name == '학생':
            user_profile = UserProfile(user=instance)
            user_profile.add_to_class('pmobileno', models.CharField(verbose_name="부모님연락처", max_length=20, unique=True, null=False))
            user_profile.add_to_class('origin', models.CharField(verbose_name="원번", max_length=20, unique=True, null=False))
            user_profile.save()

class UserProfile(models.Model):
    user = models.OneToOneField(to=User, verbose_name="사용자", on_delete=models.CASCADE)

    kor_name = models.CharField("한국이름", max_length=20, default='퍼플')
    eng_name = models.CharField("영어이름", max_length=20, default='purple')
    GENDERS = (
        ('M', '남성(Man)'),
        ('W', '여성(Woman)'),
    )
    gender = models.CharField(verbose_name="성별", max_length=1, choices=GENDERS)
    mobileno = models.CharField(verbose_name="연락처", max_length=20, unique=True)
    register_date = models.DateTimeField(verbose_name="가입일", auto_now_add=True)
    birth_year = models.PositiveIntegerField(verbose_name="출생 연도", null=True, blank=True)
    origin = models.CharField(verbose_name="원번", max_length=20, unique=True, null=True)
    pmobileno = models.CharField(verbose_name="부모님연락처", max_length=20, unique=True, null=True)

    @property
    def age(self):
        if self.birth_year:
            current_year = datetime.now().year
            return current_year - self.birth_year
        return None

    def __str__(self):
        return f"{self.user.username} 님의 프로필입니다."

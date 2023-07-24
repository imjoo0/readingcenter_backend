from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from academy.models import Academy
from datetime import datetime

class UserCategory(models.Model):
    name = models.CharField(verbose_name="카테고리 이름", max_length=50)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('사용자 아이디는 필수입니다.')
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        user_category = UserCategory.objects.get(name='퍼플아카데미')
        extra_fields.setdefault('user_category', user_category)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser):
    class Meta:
        db_table = "user"

    username = models.CharField("사용자계정",max_length=50, unique=True)
    email = models.EmailField(verbose_name="사용자 이메일", max_length=254, blank=True)
    password = models.CharField("비밀번호",max_length=128)
    user_category = models.ForeignKey(UserCategory, verbose_name="카테고리", on_delete=models.SET_NULL, null=True)
    is_staff = models.BooleanField(default=False)        
    
    REQUIRED_FIELDS = []

    objects = UserManager()

    USERNAME_FIELD = 'username'

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def __str__(self):
        return self.username

class UserProfileBase(models.Model):
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

    class Meta:
        abstract = True

    @property
    def age(self):
        if self.birth_year:
            current_year = datetime.now().year
            return current_year - self.birth_year
        return None

    def __str__(self):
        return f"{self.user.username} 프로필"
    
class Student(UserProfileBase):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    academies = models.ManyToManyField(Academy, verbose_name='다니는학원들', related_name='academy_students')
    pmobileno = models.CharField(verbose_name="부모님연락처", max_length=20, unique=True, null=True)
    origin = models.CharField(verbose_name="원번", max_length=20, unique=True, null=True)

    def __str__(self):
        return f"{self.user.username} 학생 프로필"
    
class Teacher(UserProfileBase):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    academy = models.ForeignKey(Academy, verbose_name="채용된 학원", related_name='academy_teachers', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user.username} 선생님 프로필"
    
class Manager(UserProfileBase):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    academies = models.ManyToManyField(Academy, verbose_name='관리중인 학원들', related_name='academy_manager')

    def __str__(self):
        return f"{self.user.username} 매니저 프로필"
    
class Superuser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    academies = models.ForeignKey(Academy, verbose_name='전체 학원', related_name='superuser', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user.username} 퍼플 프로필"

from django.db import models
from datetime import datetime

class AbstractUserProfile(models.Model):
    class Meta:
        db_table = "user_profile"
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

    @property
    def age(self):
        if self.birth_year:
            current_year = datetime.now().year
            return current_year - self.user.birth_year
        return None
    
    class Meta:
        abstract = True
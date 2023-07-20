from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from datetime import datetime
from branch.models import Branch


class Student(models.Model):
    # 추가적인 필드들 정의 (예: 성적 데이터 등)
    # 이 모델에서는 추상 모델인 AbstractUserProfile을 상속받지 않습니다.
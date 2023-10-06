from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# 'DJANGO_SETTINGS_MODULE' 환경 변수를 'backend.settings'로 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Celery 앱 생성
app = Celery('backend')

# Django의 설정을 사용하여 Celery 설정
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에 대한 작업을 자동으로 로드
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

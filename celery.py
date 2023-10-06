from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Django 프로젝트의 설정을 사용하기 위해 'DJANGO_SETTINGS_MODULE' 환경 변수를 설정합니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

# Celery 설정에서 Django의 설정을 사용하도록 지정합니다.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 `tasks.py`를 자동으로 찾도록 합니다.
app.autodiscover_tasks()

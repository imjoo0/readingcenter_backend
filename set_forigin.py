import os
from django.core.wsgi import get_wsgi_application

# DJANGO_SETTINGS_MODULE 환경 변수 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Django 설정 초기화
application = get_wsgi_application()

# Django 코드 실행
from django.db import connection

# 외래 키 제약 해제
with connection.cursor() as cursor:
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

# 마이그레이션 수행
# python manage.py migrate library <migration_name>

# 외래 키 제약 활성화
with connection.cursor() as cursor:
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

import csv
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from user.models import User, UserCategory

def import_users_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        for row in reader:
            username = row[0]
            # email = row[1]
            plain_password = row[1]  # 비밀번호 평문
            user_category_name = "학생"
            is_active = True
            is_staff = False
            
            # 기존 사용자 카테고리 가져오거나 생성
            user_category, _ = UserCategory.objects.get_or_create(name=user_category_name)
            
            # 사용자 객체 생성
            user = User(
                username=username,
                # email=email,
                is_active=is_active,
                is_staff=is_staff,
                user_category=user_category
            )
            user.set_password(plain_password)  # 비밀번호를 해시값으로 설정
            user.save()

# CSV 파일 경로 설정
csv_file_path = "./mnt/data/user.csv"

# CSV 파일로부터 데이터를 읽어와서 데이터베이스에 저장
import_users_from_csv(csv_file_path)

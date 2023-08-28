import csv
import os
import django
from datetime import datetime
from django.utils import timezone
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from user.models import User,Student

def import_users_from_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        for row in reader:
            kor_name = row[1]
            eng_name = row[2]
            gender = row[3]
            mobileno = row[6]
            birth_date = datetime.strptime(row[4], '%Y-%m-%d').date() if row[4] else None
            pmobileno = row[6]
            origin = row[0]

            user = User.objects.get(username = origin)
            # 사용자 객체 생성
            student = Student(
            user=user,
                kor_name=kor_name,
                eng_name=eng_name,
                gender=gender,
                mobileno=mobileno,
                register_date = timezone.now(),
                birth_date=birth_date,
                pmobileno=pmobileno,
                origin=origin,
            )
            student.save()

# CSV 파일 경로 설정
csv_file_path = "./mnt/data/user_student.csv"

# CSV 파일로부터 데이터를 읽어와서 데이터베이스에 저장
import_users_from_csv(csv_file_path)

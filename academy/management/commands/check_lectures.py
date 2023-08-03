from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from academy.models import Lecture
from student.models import Attendance
from user.models import User,Student
import pytz
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks if there are lectures starting or ending'

    def handle(self, *args, **options):
        now = timezone.now()
        now = now.astimezone(pytz.timezone('Asia/Seoul'))  # 한국 시간으로 변환
        time_threshold = timedelta(hours=12)

        lectures_starting = Lecture.objects.filter(date=now.date(), start_time__range=((now - time_threshold).time(), (now + time_threshold).time()), start_notification_sent=False)
        lectures_ending = Lecture.objects.filter(date=now.date(), end_time__range=((now - time_threshold).time(), (now + time_threshold).time()), end_notification_sent=False)

        for lecture in lectures_starting:
            # 강의 시작 알림 로직
            absent_students = []
            for student in lecture.students.all():
                target_student = Student.objects.filter(user=student).first()
                attendance = Attendance.objects.filter(student=target_student, lecture=lecture).first()
                if not attendance:
                    absent_students.append(target_student)

            if absent_students:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "notifications",
                    {
                        "type": "send_notification",
                        "message": absent_students
                    }
                )
                logger.info(f'Sent WebSocket message: {absent_students}')

            lecture.start_notification_sent = True
            lecture.save()

        for lecture in lectures_ending:
            # 강의 종료 알림 로직
            absent_students = []
            for student in lecture.students.all():
                target_student = Student.objects.filter(user=student).first()
                attendance = Attendance.objects.filter(student=target_student, lecture=lecture).first()
                if attendance and attendance.status not in ['completed', 'absent', 'makeup']:
                    absent_students.append(target_student)

            if absent_students:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "notifications",
                    {
                        "type": "send_notification",
                        "message": absent_students
                    }
                )
                logger.info(f'Sent WebSocket message: {absent_students}')
            lecture.end_notification_sent = True
            lecture.save()

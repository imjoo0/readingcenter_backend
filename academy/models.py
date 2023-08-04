from django.db import models

class Branch(models.Model):
    name = models.CharField(verbose_name="지점", max_length=50)

    def __str__(self):
        return self.name
    
class Academy(models.Model):
    name = models.CharField(verbose_name="학원 이름", max_length=100)
    location = models.CharField(verbose_name="위치", max_length=200)
    teachers = models.ForeignKey(
        'user.User',
        verbose_name="선생님",
        related_name='teacher_academy',
        on_delete=models.SET_NULL,
        null=True
    )    
    students = models.ManyToManyField(
        'user.User',
        verbose_name='학생들',
        related_name='student_academies'
    )
    manager = models.ForeignKey(
        'user.User',
        verbose_name="매니저",
        related_name='manager_academy',
        on_delete=models.SET_NULL,
        null=True
    )
    superusers = models.ManyToManyField(
        'user.Superuser',
        verbose_name="퍼플",
        related_name='purple_academies'
    )
    branch = models.OneToOneField(
        to=Branch,
        verbose_name="지점",
        related_name='academies',
        on_delete=models.SET_NULL,
        null=True
    )

    def __str__(self):
        return self.name

class Lecture(models.Model):
    DAYS_OF_WEEK = [
        (0, 'no-repeat'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    ]
    academy = models.ForeignKey(
        Academy,
        verbose_name="학원",
        related_name='lectures',
        on_delete=models.CASCADE
    )
    date = models.DateField(verbose_name="강좌 날짜")
    repeat_day = models.CharField(
        max_length=2,
        choices=DAYS_OF_WEEK,
        verbose_name="반복 요일", 
        default=0  # 기본값을 '0' (월요일)으로 설정
    )  # 이 필드는 강의가 반복되는 요일을 나타냅니다.
    start_time = models.TimeField(verbose_name="강좌 시작 시간")
    end_time = models.TimeField(verbose_name="강좌 종료 시간")
    lecture_info = models.TextField(verbose_name="강좌 설명")
    teacher = models.ForeignKey(
        'user.User',
        verbose_name="강좌 담당 선생님",
        related_name='taught_lectures',
        on_delete=models.SET_NULL,
        null=True
    )
    students = models.ManyToManyField(
        'user.User',
        verbose_name="강좌 수강 학생들",
        related_name='attended_lectures',
        blank=True
    )
    start_notification_sent = models.BooleanField(default=False)
    end_notification_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.lecture_info

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
    branch = models.ForeignKey(
        to=Branch,
        verbose_name="지점",
        related_name='academies',
        on_delete=models.SET_NULL,
        null=True
    )
    notification_interval = models.IntegerField(verbose_name="알람 전후 시간 설정",default=5)
    end_notification_custom = models.BooleanField(verbose_name="하원/등원에 커스텀",default=False)
    
    def __str__(self):
        return self.name

class LectureInfo(models.Model):
    DAYS_OF_WEEK = [
        (-1, 'no-repeat'),
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    repeat_day = models.JSONField(
        choices=DAYS_OF_WEEK,
        verbose_name="반복 요일 (JSON)",
        default=list,  # 빈 배열로 초기화
    )
    repeat_weeks = models.IntegerField(
        verbose_name="반복 주기",
        default=1  # 기본값은 매주 반복
    )
    about = models.TextField(verbose_name="강좌 설명")
    
    auto_add = models.BooleanField(default=False)
    
    def __str__(self):
        return self.lecture_info

class Lecture(models.Model):
    lecture_info = models.ForeignKey(
        LectureInfo,
        on_delete=models.CASCADE,
        related_name='lectures'
    )
    academy = models.ForeignKey(
        Academy,
        verbose_name="학원",
        related_name='lectures',
        on_delete=models.CASCADE,
        default=None
    )
    students = models.ManyToManyField(
        'user.Student',
        verbose_name="강좌 수강 학생들",
        related_name='attended_lectures',
        blank=True
    )
    teacher = models.ForeignKey(
        'user.Teacher',
        verbose_name="강좌 담당 선생님",
        related_name='taught_lectures',
        on_delete=models.SET_NULL,
        null=True
    )    
    date = models.DateField(verbose_name="강좌 날짜")
    start_time = models.TimeField(verbose_name="강좌 시작 시간",default=None)
    end_time = models.TimeField(verbose_name="강좌 종료 시간",default=None)
    lecture_memo = models.TextField(verbose_name="강좌 메모",default=None)
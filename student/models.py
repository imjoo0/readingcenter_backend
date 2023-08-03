from django.db import models
from academy.models import Lecture
from user.models import Student

# Create your models here.
class Attendance(models.Model):
    lecture = models.ForeignKey(
        Lecture, 
        verbose_name="강의",
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    student = models.ForeignKey(
        Student,
        verbose_name="학생", 
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    entry_time = models.DateTimeField(verbose_name="입장시간", null=True, blank=True)
    exit_time = models.DateTimeField(verbose_name="퇴장시간", null=True, blank=True)
    STATUS_CHOICES = (
        ('attendance', '등원'),
        ('completed', '완료'),
        ('cancelled', '취소'),
        ('late', '지각'),
        ('absent', '결석'),
        ('makeup', '보강'),
    )
    status = models.CharField(
        verbose_name="상태", 
        max_length=10, 
        choices=STATUS_CHOICES,
        default='absent'
    )

    def __str__(self):
        return f"{self.lecture.lecture_info} - {self.student.username}"

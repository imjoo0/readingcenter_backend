from django.db import models
from academy.models import Lecture
from user.models import Student
from library.models import Book
from django.utils import timezone

# Create your models here.
class Attendance(models.Model):
    lecture = models.ForeignKey(
        Lecture, 
        verbose_name="강의",
        on_delete=models.CASCADE,
        # related_name='attendances'
        related_name='attendance'
    )
    student = models.ForeignKey(
        Student,
        verbose_name="학생", 
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    entry_time = models.DateTimeField(verbose_name="입장시간", null=True, blank=True)
    exit_time = models.DateTimeField(verbose_name="퇴장시간", null=True, blank=True)
    memo = models.TextField(verbose_name="강의 메모", null=True, blank=True)
    
    STATUS_CHOICES = (
        ('attendance', '등원'),
        ('completed', '하원'),
        ('cancelled', '취소'),
        ('late', '지각'),
        ('absent', '결석'),
        ('makeup', '결석 (보강)'),
    )
    status = models.CharField(
        verbose_name="상태", 
        max_length=10, 
        choices=STATUS_CHOICES,
        default=None,
        null=True
    )

    def __str__(self):
        return f"{self.lecture.lecture_info} - {self.student.kor_name}"

class BookRecord(models.Model):
    student = models.ForeignKey(
        Student,
        verbose_name="학생", 
        on_delete=models.CASCADE,
        related_name='book_records'
    )
    origin = models.CharField(verbose_name="원번", max_length=20, unique=True, null=True)
    book =  models.ForeignKey(
        Book, 
        verbose_name="읽은 도서",
        on_delete=models.CASCADE,
        related_name='student_records'
    )
    ar_correct = models.IntegerField(null=True, blank=True)
    ar_date = models.DateField(verbose_name="ar 퀴즈푼 날짜", null=True, blank=True)
    lit_correct = models.IntegerField(null=True, blank=True)
    lit_date = models.DateField(verbose_name="lit 퀴즈푼 날짜", null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)

class MonthReport(models.Model):
    student = models.ForeignKey(
        Student,
        verbose_name="학생", 
        on_delete=models.CASCADE,
        related_name='month_report'
    )
    origin = models.CharField(verbose_name="원번", max_length=20,null=False)
    month = models.IntegerField(null=True, blank=True)
    bc = models.IntegerField(null=True, blank=True)
    wc = models.IntegerField(null=True, blank=True)
    ar = models.FloatField(null=True, blank=True)
    wc_per_book = models.FloatField(null=True, blank=True)
    correct = models.IntegerField(null=True, blank=True)
    update_time = models.CharField(verbose_name="update_time", max_length=45, null=False)

class SummaryReport(models.Model):
    student = models.ForeignKey(
        Student,
        verbose_name="학생", 
        on_delete=models.CASCADE,
        related_name='summary_report'
    )
    origin = models.CharField(verbose_name="원번", max_length=20,null=False)
    recent_study_date = models.DateField(verbose_name="최근 학습 일", null=True, blank=True)
    this_month_ar = models.FloatField(null=True, blank=True)
    last_month_ar = models.FloatField(null=True, blank=True)
    ar_diff = models.FloatField(null=True, blank=True)
    this_month_wc = models.IntegerField(null=True, blank=True)
    last_month_wc = models.IntegerField(null=True, blank=True)
    total_wc = models.IntegerField(null=True, blank=True)
    this_month_correct = models.IntegerField(null=True, blank=True)
    last_month_correct = models.IntegerField(null=True, blank=True)
    total_correct = models.IntegerField(null=True, blank=True)
    this_month_bc = models.IntegerField(null=True, blank=True)
    last_month_bc = models.IntegerField(null=True, blank=True)
    total_bc = models.IntegerField(null=True, blank=True)
    this_month_study_days = models.IntegerField(null=True, blank=True)
    last_month_study_days = models.IntegerField(null=True, blank=True)
    total_study_days = models.IntegerField(null=True, blank=True)
    update_time = models.DateTimeField(default=timezone.now)
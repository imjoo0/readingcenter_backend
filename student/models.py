from django.db import models
from academy.models import Lecture
from user.models import Student
from library.models import Book

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
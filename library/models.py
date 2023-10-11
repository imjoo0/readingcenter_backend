from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords
from academy.models import Academy,Lecture
from user.models import User, Student 

class Book(models.Model):
    id = models.IntegerField(unique=True, primary_key=True) 
    kplbn = models.IntegerField(unique=True)
    title_ar = models.CharField(max_length=255, null=True)
    author_ar = models.CharField(max_length=255, null=True)
    title_lex = models.CharField(max_length=255, null=True)
    author_lex = models.CharField(max_length=255, null=True)
    FNF = (
        ('0', 'F_NF'),
        ('1', 'F'),
        ('2', 'NF'),
    )
    fnf = models.CharField(
        verbose_name="FNF", 
        max_length=10, 
        choices=FNF,
        null=True
    )
    IL = (
        ('0', 'IL'),
        ('1', 'IL_LG'),
        ('2', 'IL_MG'),
        ('3', 'IL_MG+'),
        ('4', 'IL_UG'),
    )
    il = models.CharField(
        verbose_name="IL", 
        max_length=10, 
        choices=IL,
        null=True
    )
    LITPRO = (
        ('0', 'LITPRO'),
        ('1', 'LITPRO_Y'),
        ('2', 'LITPRO_N'),
    )
    litpro = models.CharField(
        verbose_name="LITPRO", 
        max_length=10, 
        choices=LITPRO,
        default=0
    )
    LEXILE_CODE_AR = (
        ('0', 'LEXILE_CODE_AR'),
        ('1', 'LEXILE_CODE_AR_AD'),
        ('2', 'LEXILE_CODE_AR_GN'),
        ('3', 'LEXILE_CODE_AR_HL'),
        ('4', 'LEXILE_CODE_AR_IG'),
        ('5', 'LEXILE_CODE_AR_NC'),
        ('6', 'LEXILE_CODE_AR_NP'),
        ('7', 'LEXILE_CODE_AR_RA'),
    )
    lexile_code_ar = models.CharField(
        verbose_name="LEXILE_CODE_AR", 
        max_length=10, 
        choices=LEXILE_CODE_AR,
        null=True
    )
    LEXILE_CODE_LEX = (
        ('0', 'LEXILE_CODE_LEX'),
        ('1', 'LEXILE_CODE_LEX_AD'),
        ('2', 'LEXILE_CODE_LEX_GN'),
        ('3', 'LEXILE_CODE_LEX_HL'),
        ('4', 'LEXILE_CODE_LEX_IG'),
        ('5', 'LEXILE_CODE_LEX_NC'),
        ('6', 'LEXILE_CODE_LEX_NP'),
        ('7', 'LEXILE_CODE_LEX_RA'),
    )
    lexile_code_lex = models.CharField(
        verbose_name="LEXILE_CODE_LEX", 
        max_length=10, 
        choices=LEXILE_CODE_LEX,
        null=True
    )
    ar_quiz = models.IntegerField(null=True, blank=True)
    ar_pts = models.FloatField(null=True, blank=True)
    bl = models.FloatField(null=True, blank=True)
    wc_ar = models.IntegerField(null=True, blank=True)
    wc_lex = models.IntegerField(null=True, blank=True)
    lexile_ar = models.IntegerField(null=True, blank=True)
    lexile_lex = models.IntegerField(null=True, blank=True)

class BookInventory(models.Model):
    STATUS_CHOICES = [
        (0, '정상'),
        (1, '파손'),
        (2, '분실'),
    ]
    plbn = models.CharField(max_length=100,null=True)
    academy = models.ForeignKey(Academy, on_delete=models.SET_NULL, related_name='book_inventories', null=True)
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='books', null=True)
    box_number = models.CharField(max_length=255)
    place = models.TextField(blank=True, null=True)
    isbn = models.BigIntegerField(verbose_name="바코드", null=True, blank=True)
    updatetime = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, null=True)

    history = HistoricalRecords()

class BookRental(models.Model):
    book_inventory = models.ForeignKey(BookInventory, on_delete=models.PROTECT, related_name='rentals', null=True)
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='rented_books')
    rented_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    memo = models.TextField(blank=True, null=True)

class BookReservation(models.Model):
    # lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='book_reservations')
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='book_reservation_list')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_reservations')
    books = models.ManyToManyField(BookInventory, related_name='reservations')

class BookPkg(models.Model):
    name = models.CharField(verbose_name="패키지 이름", max_length=255)
    books = models.ManyToManyField(Book, verbose_name="도서들", related_name="packages")
    fnf = models.IntegerField(null=True) # 0:F_NF 1:F 2:NF 
    
    ar_min = models.FloatField(verbose_name="최소 AR 점수") # library_book 테이블의 bl 평균값으로 비교 
    ar_max = models.FloatField(verbose_name="최대 AR 점수")
    
    wc_min = models.IntegerField(verbose_name="최소 WC") # library_book 테이블의 wc_ar 평균값으로 비교
    wc_max = models.IntegerField(verbose_name="최대 WC")
    
    correct_min = models.IntegerField(verbose_name="최소 정답률") # student_book_reacord 테이블의 ar_correct 평균값으로 비교
    correct_max = models.IntegerField(verbose_name="최대 정답률")

    il = models.CharField(
        verbose_name="IL", 
        max_length=10, 
        null=True
    ) #IL 값에 따라 추천 도서 수인 il_count가 다름 
    # IL = (
    #     ('1', 'IL_LG'),
    #     ('2', 'IL_MG'),
    #     ('3', 'IL_MG+'),
    #     ('4', 'IL_UG'),
    # )
    il_count = models.IntegerField(null=False)

    def __str__(self):
        return self.name
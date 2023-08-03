from django.db import models
from django.utils import timezone
from academy.models import Academy,Lecture
from user.models import User, Student 

class Book(models.Model):
    kplnbn = models.IntegerField(unique=True)
    title_ar = models.CharField(max_length=255)
    author_ar = models.CharField(max_length=255)
    title_lex = models.CharField(max_length=255)
    author_lex = models.CharField(max_length=255)
    FNF = (
        (0, 'F_NF'),
        (1, 'F'),
        (2, 'NF'),
    )
    fnf = models.CharField(
        verbose_name="FNF", 
        max_length=10, 
        choices=FNF,
        default=0
    )
    IL = (
        (0, 'IL'),
        (1, 'IL_LG'),
        (2, 'IL_MG'),
        (3, 'IL_MG+'),
        (4, 'IL_UG'),
    )
    il = models.CharField(
        verbose_name="IL", 
        max_length=10, 
        choices=IL,
        default=0
    )
    LITPRO = (
        (0, 'LITPRO'),
        (1, 'LITPRO_Y'),
        (2, 'LITPRO_N'),
    )
    litpro = models.CharField(
        verbose_name="LITPRO", 
        max_length=10, 
        choices=LITPRO,
        default=0
    )
    LEXILE_CODE_AR = (
        (0, 'LEXILE_CODE_AR'),
        (1, 'LEXILE_CODE_AR_AD'),
        (2, 'LEXILE_CODE_AR_GN'),
        (3, 'LEXILE_CODE_AR_HL'),
        (4, 'LEXILE_CODE_AR_IG'),
        (5, 'LEXILE_CODE_AR_NC'),
        (6, 'LEXILE_CODE_AR_NP'),
        (7, 'LEXILE_CODE_AR_RA'),
    )
    lexile_code_ar = models.CharField(
        verbose_name="LEXILE_CODE_AR", 
        max_length=10, 
        choices=LEXILE_CODE_AR,
        default=0
    )
    LEXILE_CODE_LEX = (
        (0, 'LEXILE_CODE_LEX'),
        (1, 'LEXILE_CODE_LEX_AD'),
        (2, 'LEXILE_CODE_LEX_GN'),
        (3, 'LEXILE_CODE_LEX_HL'),
        (4, 'LEXILE_CODE_LEX_IG'),
        (5, 'LEXILE_CODE_LEX_NC'),
        (6, 'LEXILE_CODE_LEX_NP'),
        (7, 'LEXILE_CODE_LEX_RA'),
    )
    lexile_code_lex = models.CharField(
        verbose_name="LEXILE_CODE_LEX", 
        max_length=10, 
        choices=LEXILE_CODE_LEX,
        default=0
    )
    ar_quiz = models.IntegerField(null=True, blank=True)
    ar_pts = models.FloatField(null=True, blank=True)
    bl = models.FloatField(null=True, blank=True)
    wc_ar = models.IntegerField(null=True, blank=True)
    wc_lex = models.IntegerField(null=True, blank=True)
    lexile_ar = models.IntegerField(null=True, blank=True)
    lexile_lex = models.IntegerField(null=True, blank=True)

class BookInventory(models.Model):
    plbn = models.IntegerField(null=True)
    academy = models.ForeignKey(Academy, on_delete=models.SET_NULL, related_name='book_inventories', null=True)
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='books')
    box_number = models.CharField(max_length=255)
    place = models.TextField(blank=True, null=True)
    isbn = models.IntegerField(verbose_name="바코드",default=0)
    updatetime = models.DateTimeField(default=timezone.now)

class BookRental(models.Model):
    book_inventory = models.ForeignKey(BookInventory, on_delete=models.PROTECT, related_name='rentals', null=True)
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='rented_books')
    rented_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    memo = models.TextField(blank=True, null=True)

class BookReservation(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.PROTECT, related_name='book_reservations')
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='book_reservations')
    books = models.ManyToManyField(BookInventory, related_name='reservations')


import csv
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from library.models import Book

with open('./mnt/data/BOOK.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # Skip the header row
    for row in reader:
        _, created = Book.objects.get_or_create(
            kplnbn=int(row[0]),
            title_ar=row[1],
            author_ar=row[2],
            title_lex=row[3],
            author_lex=row[4],
            fnf=row[5],
            il=row[6],
            litpro=row[7],
            lexile_code_ar=row[8],
            lexile_code_lex=row[9],
            ar_quiz=int(row[10]) if row[10] else None,
            ar_pts=float(row[11]) if row[11] else None,
            bl=float(row[12]) if row[12] else None,
            wc_ar=int(row[13]) if row[13] else None,
            wc_lex=int(row[14]) if row[14] else None,
            lexile_ar=int(row[15]) if row[15] else None,
            lexile_lex=int(row[16]) if row[16] else None
        )

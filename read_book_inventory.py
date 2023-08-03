import csv
import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from library.models import Book, BookInventory

with open('./mnt/data/BOOKINVENTORY.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # Skip the header row
    for row in reader:
        try:
            book = Book.objects.get(kplnbn=row[0])  # Assuming kplnbn is the first column
        except Book.DoesNotExist:
            print(f"Book with kplnbn {row[0]} does not exist.")
            continue  # Skip this row and go to the next one # Assuming kplnbn is the first column
        _, created = BookInventory.objects.get_or_create(
            book=book,
            academy_id=1,
            plbn = int(row[1]),  # Assuming academy id is the second column
            isbn=int(row[2]),  # Assuming isbn is the fifth column # Assuming possetion is the sixth column
            box_number=row[3],  # Assuming box_number is the third column
            updatetime=timezone.now()
        )

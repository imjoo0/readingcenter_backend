from django.shortcuts import render, redirect
from .forms import BookForm
from book.models import Book

def create_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'myapp/template/create_book.html', {'form': form})
# {{ form.as_p }}

def book_list(request):
    books = Book.objects.all()
    return render(request, 'myapp/template/book_list.html', {'books': books})
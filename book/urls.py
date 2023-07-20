from django.contrib import admin
from django.urls import path, include
from .views import create_book, book_list

urlpatterns = [
    path('create/', create_book, name='create_book'),
    path('list/', book_list, name='book_list'),
]
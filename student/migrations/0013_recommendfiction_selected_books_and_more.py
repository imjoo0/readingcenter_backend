# Generated by Django 4.2.3 on 2023-10-20 01:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0007_alter_bookpkg_il_count'),
        ('student', '0012_opinion'),
    ]

    operations = [
        migrations.AddField(
            model_name='recommendfiction',
            name='selected_books',
            field=models.ManyToManyField(blank=True, related_name='recommend_fictions', to='library.book', verbose_name='선택된 도서들'),
        ),
        migrations.AddField(
            model_name='recommendnonfiction',
            name='selected_books',
            field=models.ManyToManyField(blank=True, related_name='recommend_nonfictions', to='library.book', verbose_name='선택된 도서들'),
        ),
    ]

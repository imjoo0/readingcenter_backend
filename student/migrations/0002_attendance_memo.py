# Generated by Django 4.2.3 on 2023-08-24 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='memo',
            field=models.TextField(blank=True, null=True, verbose_name='강의 메모'),
        ),
    ]

# Generated by Django 4.2.3 on 2023-10-04 05:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0008_lectureinfo_created_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lecture',
            name='lecture_memo',
            field=models.TextField(default=None, null=True, verbose_name='보강 강좌 메모'),
        ),
    ]
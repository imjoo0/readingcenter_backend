# Generated by Django 4.2.3 on 2023-10-09 23:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0006_bookpkg'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookpkg',
            name='il_count',
            field=models.IntegerField(),
        ),
    ]

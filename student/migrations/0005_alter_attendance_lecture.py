# Generated by Django 4.2.3 on 2023-09-27 01:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0006_alter_lecture_academy_alter_lecture_lecture_info_and_more'),
        ('student', '0004_alter_monthreport_ar_alter_monthreport_correct_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='lecture',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance', to='academy.lecture', verbose_name='강의'),
        ),
    ]

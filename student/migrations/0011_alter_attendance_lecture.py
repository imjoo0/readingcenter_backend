# Generated by Django 4.2.3 on 2023-10-06 08:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0009_alter_lecture_lecture_memo'),
        ('student', '0010_alter_attendance_lecture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='lecture',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='attendance', to='academy.lecture', verbose_name='강의'),
        ),
    ]

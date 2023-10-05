# Generated by Django 4.2.3 on 2023-09-27 01:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
        ('academy', '0005_remove_lectureinfo_academy_lecture_academy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lecture',
            name='academy',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='academy_lectures', to='academy.academy', verbose_name='학원'),
        ),
        migrations.AlterField(
            model_name='lecture',
            name='lecture_info',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lectureList', to='academy.lectureinfo'),
        ),
        migrations.AlterField(
            model_name='lecture',
            name='students',
            field=models.ManyToManyField(blank=True, related_name='enrolled_lectures', to='user.student', verbose_name='강좌 수강 학생들'),
        ),
        migrations.AlterField(
            model_name='lecture',
            name='teacher',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teacher_lectures', to='user.teacher', verbose_name='강좌 담당 선생님'),
        ),
    ]
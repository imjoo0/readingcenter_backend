# Generated by Django 4.2.3 on 2023-07-26 12:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academy', '0003_lecture'),
        ('user', '0005_remove_superuser_academies_superuser_academies'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_time', models.DateTimeField(blank=True, null=True, verbose_name='입장시간')),
                ('exit_time', models.DateTimeField(blank=True, null=True, verbose_name='퇴장시간')),
                ('status', models.CharField(choices=[('completed', '완료'), ('cancelled', '취소'), ('absent', '결석')], default='absent', max_length=10, verbose_name='상태')),
                ('lecture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='academy.lecture', verbose_name='강의')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='user.student', verbose_name='학생')),
            ],
        ),
    ]

# Generated by Django 4.2.3 on 2023-10-23 05:56

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academy', '0009_alter_lecture_lecture_memo'),
        ('user', '0001_initial'),
        ('student', '0016_summaryreport_base_date_summaryreport_last_month_sr_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='lecture',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attendance', to='academy.lecture', verbose_name='강의'),
        ),
        migrations.CreateModel(
            name='Consulting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(verbose_name='상담 제목')),
                ('contents', models.TextField(verbose_name='상담 내용')),
                ('created_at', models.DateField(blank=True, default=datetime.date.today, null=True, verbose_name='상담 생성 날짜')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consulting_student', to='user.student', verbose_name='학생')),
                ('writer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consulting_writer', to=settings.AUTH_USER_MODEL, verbose_name='작성자')),
            ],
        ),
    ]
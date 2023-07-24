# Generated by Django 4.2.3 on 2023-07-24 04:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0001_initial'),
        ('user', '0002_user_is_staff_user_is_superuser_userprofile_origin_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Manager',
            fields=[
                ('kor_name', models.CharField(default='퍼플', max_length=20, verbose_name='한국이름')),
                ('eng_name', models.CharField(default='purple', max_length=20, verbose_name='영어이름')),
                ('gender', models.CharField(choices=[('M', '남성(Man)'), ('W', '여성(Woman)')], max_length=1, verbose_name='성별')),
                ('mobileno', models.CharField(max_length=20, unique=True, verbose_name='연락처')),
                ('register_date', models.DateTimeField(auto_now_add=True, verbose_name='가입일')),
                ('birth_year', models.PositiveIntegerField(blank=True, null=True, verbose_name='출생 연도')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('academies', models.ManyToManyField(related_name='academy_manager', to='academy.academy', verbose_name='관리중인 학원들')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('kor_name', models.CharField(default='퍼플', max_length=20, verbose_name='한국이름')),
                ('eng_name', models.CharField(default='purple', max_length=20, verbose_name='영어이름')),
                ('gender', models.CharField(choices=[('M', '남성(Man)'), ('W', '여성(Woman)')], max_length=1, verbose_name='성별')),
                ('mobileno', models.CharField(max_length=20, unique=True, verbose_name='연락처')),
                ('register_date', models.DateTimeField(auto_now_add=True, verbose_name='가입일')),
                ('birth_year', models.PositiveIntegerField(blank=True, null=True, verbose_name='출생 연도')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('pmobileno', models.CharField(max_length=20, null=True, unique=True, verbose_name='부모님연락처')),
                ('origin', models.CharField(max_length=20, null=True, unique=True, verbose_name='원번')),
                ('academies', models.ManyToManyField(related_name='academy_students', to='academy.academy', verbose_name='다니는학원들')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Superuser',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('academies', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='superuser', to='academy.academy', verbose_name='전체 학원')),
            ],
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('kor_name', models.CharField(default='퍼플', max_length=20, verbose_name='한국이름')),
                ('eng_name', models.CharField(default='purple', max_length=20, verbose_name='영어이름')),
                ('gender', models.CharField(choices=[('M', '남성(Man)'), ('W', '여성(Woman)')], max_length=1, verbose_name='성별')),
                ('mobileno', models.CharField(max_length=20, unique=True, verbose_name='연락처')),
                ('register_date', models.DateTimeField(auto_now_add=True, verbose_name='가입일')),
                ('birth_year', models.PositiveIntegerField(blank=True, null=True, verbose_name='출생 연도')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('academy', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='academy_teachers', to='academy.academy', verbose_name='채용된 학원')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_staff',
        ),
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]

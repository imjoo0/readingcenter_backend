# Generated by Django 4.2.3 on 2023-08-04 01:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0005_lecture_end_notification_sent_and_more'),
        ('user', '0007_alter_manager_user_alter_student_user_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Remark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memo', models.TextField()),
                ('academy', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='memo', to='academy.academy', verbose_name='학원')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='memo', to=settings.AUTH_USER_MODEL, verbose_name='회원')),
            ],
        ),
    ]
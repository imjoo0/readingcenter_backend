# Generated by Django 4.2.3 on 2023-08-02 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0004_lecture_repeat_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='lecture',
            name='end_notification_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lecture',
            name='start_notification_sent',
            field=models.BooleanField(default=False),
        ),
    ]
# Generated by Django 4.2.3 on 2023-09-26 08:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0004_remove_lectureinfo_end_time_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lectureinfo',
            name='academy',
        ),
        migrations.AddField(
            model_name='lecture',
            name='academy',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='lectures', to='academy.academy', verbose_name='학원'),
        ),
    ]

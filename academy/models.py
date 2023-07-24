from django.db import models

class Branch(models.Model):
    name = models.CharField(verbose_name="지점", max_length=50)

    def __str__(self):
        return self.name
    
class Academy(models.Model):
    name = models.CharField(verbose_name="학원 이름", max_length=100)
    location = models.CharField(verbose_name="위치", max_length=200)
    teachers = models.ForeignKey(
        'user.User',
        verbose_name="선생님",
        related_name='teacher_academy',
        on_delete=models.SET_NULL,
        null=True
    )    
    students = models.ManyToManyField(
        'user.User',
        verbose_name='학생들',
        related_name='student_academies'
    )
    manager = models.ForeignKey(
        'user.User',
        verbose_name="매니저",
        related_name='manager_academy',
        on_delete=models.SET_NULL,
        null=True
    )
    branch = models.OneToOneField(
        to=Branch,
        verbose_name="지점",
        related_name='academies',
        on_delete=models.SET_NULL,
        null=True
    )

    def __str__(self):
        return self.name
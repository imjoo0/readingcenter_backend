from django.db import models

# Create your models here.
class UserModel(models.Model):
    class Meta:
        db_table = "user"

    user_id = models.CharField(max_length=50, null=False)
    user_pw = models.CharField(max_length=256, null=False)
    category_id = models.IntegerField()
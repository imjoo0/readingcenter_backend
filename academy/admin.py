from django.contrib import admin
from .models import(
    Branch as BranchModel,
    Academy as AcademyModel
)

# Register your models here.
admin.site.register(BranchModel)
admin.site.register(AcademyModel)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from user.models import User as UserModel, UserCategory as UserCategoryModel
from user.models import (
    Student as StudentModel,
    Teacher as TeacherModel,
    Manager as ManagerModel,
    Superuser as SuperuserModel,
)
class StudentInline(admin.StackedInline):
    model = StudentModel

class TeacherInline(admin.StackedInline):
    model = TeacherModel

class ManagerInline(admin.StackedInline):
    model = ManagerModel

class SuperuserInline(admin.StackedInline):
    model = SuperuserModel

class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'user_category')
    list_display_links = ('username', )
    list_filter = ('username', )
    search_fields = ('username', 'email', )

    fieldsets = (
        ("info", {'fields': ('username', 'password', 'email',)}),
        ('permissions', {'fields':( 'is_staff', )}),
    )

    filter_horizontal = []

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('username', 'join_date')
        else:
            return ('join_date',)

    def get_inline_instances(self, request, obj=None):
        if obj:
            if obj.user_category.name == '학생':
                return [StudentInline(self.model, self.admin_site)]
            elif obj.user_category.name == '선생님':
                return [TeacherInline(self.model, self.admin_site)]
            elif obj.user_category.name == '매니저':
                return [ManagerInline(self.model, self.admin_site)]
            else:
                return[SuperuserInline(self.model,self.admin_site)]
        return []

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_category', 'password1', 'password2'),
        }),
    )

admin.site.register(UserModel, UserAdmin)
# admin.site.register(StudentModel)
# admin.site.register(TeacherModel)
# admin.site.register(ManagerModel)
admin.site.register(UserCategoryModel)

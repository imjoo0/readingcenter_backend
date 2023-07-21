from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from user.models import User as UserModel, UserProfile as UserProfileModel, UserCategory as UserCategoryModel

class UserProfileInline(admin.StackedInline):
    model = UserProfileModel

class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'user_category')
    list_display_links = ('username', )
    list_filter = ('username', )
    search_fields = ('username', 'email', )

    fieldsets = (
        ("info", {'fields': ('username', 'password', 'email',)}),
        ('permissions', {'fields':('is_staff', 'is_superuser', )}),
    )

    filter_horizontal = []

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('username', )
        else:
            return ('join_date',)

    inlines = (UserProfileInline,)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_category', 'password1', 'password2'),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.user_category.name == '학생':
            try:
                user_profile = obj.userprofile
            except UserProfileModel.DoesNotExist:
                user_profile = UserProfileModel(user=obj)
                user_profile.pmobileno = "부모님연락처"
                user_profile.origin = "원번"
                user_profile.save()

admin.site.register(UserModel, UserAdmin)
admin.site.register(UserProfileModel)
admin.site.register(UserCategoryModel)

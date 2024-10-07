from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import Account, UserProfile
from django.utils.html import format_html

import admin_thumbnails

class AccountAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'username', 'last_login', 'date_joined', 'is_active', ]
    list_display_links = ['email', 'first_name', 'last_name']
    readonly_fields = ['last_login', 'date_joined']
    ordering = ['-date_joined']
    
    filter_horizontal = []
    list_filter = []
    fieldsets = []


#@admin_thumbnails.thumbnail('profile_picture')
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'state', 'country', 'full_address', 'thumbnail']
    
    def thumbnail(self, object):
        return format_html("<img src='{}' width='30' style = 'border-radius:50%'>".format(object.profile_picture.url))
    thumbnail.short_description = "Profile Picture"
    

admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

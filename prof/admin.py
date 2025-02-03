from django.contrib import admin
from .models import UserProfile ,Posts , WorkerInvitation , UsersCategory , CityCategory , PostsCategory
# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Posts)
admin.site.register(WorkerInvitation)
admin.site.register(UsersCategory)
admin.site.register(CityCategory)
admin.site.register(PostsCategory)
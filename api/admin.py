from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Exercise, Workout, Profile, SleepLog



admin.site.register(User, UserAdmin)
admin.site.register(Exercise)
admin.site.register(Workout)
admin.site.register(Profile)
admin.site.register(SleepLog)

# Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Exercise, Workout, Profile, SleepLog, NutritionPlan



admin.site.register(User, UserAdmin)
admin.site.register(Exercise)
admin.site.register(Workout)
admin.site.register(Profile)
admin.site.register(SleepLog)
@admin.register(NutritionPlan)
class NutritionPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_calories', 'target_protein', 'created_at')
    search_fields = ('user__username', 'user__email')

# Register your models here.

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from api.views import get_heatmap_data

urlpatterns = [
    path('status/', views.check_status),
    path('users/', views.handle_register),
    path('workouts/', views.handle_workouts), 
    path('workouts/<int:pk>/', views.workout_detail),
    
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('exercises/', views.handle_exercises, name='exercises'),
    path('exercises/<int:pk>/', views.exercise_detail, name='exercise_detail'),
    path('profile/', views.handle_profile, name='profile'),
    path('weight-logs/', views.handle_weight_logs, name='weight_logs'),
    path('heatmap/', get_heatmap_data, name='heatmap_data'),
    
    # ▼▼▼ NUEVA RUTA DE STRIPE ▼▼▼
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('create-customer-portal/', views.create_customer_portal, name='create_customer_portal'),
    #GOOGLE LOGIN
    path('google-login/', views.google_login, name='google_login'),
    path('update-nutrition/', views.update_nutrition_profile),
    path('save-sleep/', views.save_sleep_log, name='save_sleep_log'),
    path('voice-workout/', views.process_voice_workout),
    path('templates/', views.handle_templates, name='handle_templates'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('predict-workout/', views.predict_next_workout, name='predict_workout'),
    
    
    
]
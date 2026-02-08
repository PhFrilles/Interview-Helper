from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('login/', views.login, name='login'), 
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),
    path('interview/', views.interview, name='interview'),
    path('createQuestion/', views.createQuestion, name='createQuestion'),
    
    # NEW PATHS TO ADD:
    path('analyze-interview/', views.analyze_interview, name='analyze_interview'),
    path('system-status/', views.system_status, name='system_status'),
    path('test-gemini/', views.test_gemini_connection, name='test_gemini'),
    path('logout/', views.logout, name='logout'),
    path('session/success/', views.session_success, name='session_success'),
    path('session/cancel/', views.session_cancel, name='session_cancel'),
]   
from django.urls import path
from .views import health_check, login

app_name = 'core'

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('auth/login/', login, name='login'),
]

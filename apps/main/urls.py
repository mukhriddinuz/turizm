from django.urls import path
from .views import HomeAPIView

app_name = 'main'

urlpatterns = [
    path('home/', HomeAPIView.as_view(), name='home'),
]
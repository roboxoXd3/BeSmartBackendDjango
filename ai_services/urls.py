from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat, name='ai-chat'),
    path('image-search/', views.analyze_image, name='ai-image-search'),
]

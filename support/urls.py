from django.urls import path
from .views import message_list_create, message_detail

urlpatterns = [
    path('messages/', message_list_create),
    path('messages/<int:pk>/', message_detail),
]
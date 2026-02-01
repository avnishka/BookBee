from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),
    path('start/<str:username>/', views.start_chat, name='start_chat'),
    path('delete/<int:room_id>/', views.delete_chat, name='delete_chat'),
    path('start/<str:username>/', views.start_chat, name='start_chat'),
    path('delete/<int:room_id>/', views.delete_chat, name='delete_chat'),
]
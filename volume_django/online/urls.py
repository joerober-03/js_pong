from . import views
from django.urls import path

urlpatterns = [
    path('room/', views.CreateRoom, name='create-room'),
    path('test/', views.test, name='test'),
    # path('api/<str:room_name>/', views.message_list),
    # path('api/<str:room_name>/<str:username>/', views.user_message_list),
    ]

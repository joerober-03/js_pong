from django.shortcuts import render, redirect
from .models import *
from django.http import JsonResponse
# import time

def CreateRoom(request):

    if request.method == 'POST':
        username = request.POST['username']
        room = request.POST['room']

        if (room.strip() == "" or username.strip() == ""):
            context = {
                "error": "Please enter a valid username and room name",
            }
            return render(request, 'chat/index.html', context)

        try:
            get_room = Room.objects.get(room_name=room)
            if get_room.full == True:
                context = {
                    "error": "This room is full, please try another one",
                }
                return render(request, 'chat/index.html', context)
            return redirect('room', room_name=room, username=username)

        except Room.DoesNotExist:
            new_room = Room(room_name = room)
            new_room.save()
            return redirect('room', room_name=room, username=username)
    
    context = {
        "error": "",
    }

    return render(request, 'chat/index.html', context)

def PongView(request, room_name, username):
    try:
        get_room = Room.objects.get(room_name=room_name)
        if get_room.full == True:
            context = {
                "error": "full",
            }
            return render(request, 'chat/noRoom.html', context)
        context = {
            "user": username,
            "room_name": room_name,
        }
        return render(request, 'chat/pong.html', context)

    except Room.DoesNotExist:
        context = {
                "error": "noRoom",
            }
        return render(request, 'chat/noRoom.html', context)
    return render(request, 'chat/pong.html')

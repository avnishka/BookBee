from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import ChatRoom, Message


@login_required
def chat_list(request):
    rooms = ChatRoom.objects.filter(user1=request.user) | ChatRoom.objects.filter(user2=request.user)
    return render(request, 'chat/chat_list.html', {'rooms': rooms})


@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.user != room.user1 and request.user != room.user2:
        return redirect('home')

    if request.method == 'POST':
        Message.objects.create(
            room=room,
            sender=request.user,
            text=request.POST.get('message')
        )

    messages = room.messages.order_by('timestamp')
    other_user = room.user2 if room.user1 == request.user else room.user1

    return render(request, 'chat/chat_room.html', {
        'room': room,
        'messages': messages,
        'other_user': other_user
    })


@login_required
def start_chat(request, username):
    other_user = get_object_or_404(User, username=username)

    room = ChatRoom.objects.filter(user1=request.user, user2=other_user).first() \
        or ChatRoom.objects.filter(user1=other_user, user2=request.user).first()

    if not room:
        room = ChatRoom.objects.create(user1=request.user, user2=other_user)

    return redirect('chat_room', room.id)
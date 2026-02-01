from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import ChatRoom, Message
from django.db.models import Count, Q


from django.db.models import Count, Q

@login_required
def chat_list(request):
    rooms = ChatRoom.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).annotate(
        unread_count=Count(
            'message',
            filter=Q(message__is_read=False) & ~Q(message__sender=request.user)
        )
    )

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

    messages = room.message_set.order_by('created_at')
    # Mark messages sent to this user as read
    messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    other_user = room.user2 if room.user1 == request.user else room.user1

    return render(request, 'chat/chat_room.html', {
        'room': room,
        'messages': messages,
        'other_user': other_user
    })


@login_required
def delete_chat(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)

    # Only allow participants to delete
    if request.user == room.user1 or request.user == room.user2:
        room.delete()

    return redirect('chat_list')


@login_required
def start_chat(request, username):
    other_user = get_object_or_404(User, username=username)

    # Prevent chatting with yourself
    if other_user == request.user:
        return redirect('chat_list')

    # Ensure consistent ordering so same room is reused
    user1, user2 = sorted([request.user, other_user], key=lambda u: u.id)

    room, created = ChatRoom.objects.get_or_create(user1=user1, user2=user2)

    return redirect('chat_room', room_id=room.id)

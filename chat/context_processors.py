from .models import Message
from django.db.models import Q

def unread_messages_count(request):
    if request.user.is_authenticated:
        # Count messages where:
        # 1. It is NOT read
        # 2. You are NOT the sender
        # 3. You are part of the room
        count = Message.objects.filter(is_read=False).exclude(sender=request.user).filter(
            Q(room__user1=request.user) | Q(room__user2=request.user)
        ).count()
        
        return {'total_unread_messages': count}
    return {'total_unread_messages': 0}
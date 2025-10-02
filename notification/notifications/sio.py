import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

@sio.event
async def connect(sid, environ, auth):
    user_id = auth.get("user_id") if auth else None
    if user_id:
        await sio.save_session(sid, {"user_id": user_id})
        await sio.enter_room(sid, f"user_{user_id}")
        print(f"✅ User {user_id} connected via Socket.IO")
    else:
        return False  # Reject if no user_id

@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    print(f"❌ User {user_id} disconnected")

@sio.event
async def mark_read(sid, data):
    from .models import Notification  # 👈 Import inside the function
    notif_id = data.get("id")
    try:
        notif = Notification.objects.get(id=notif_id)
        notif.is_read = True
        notif.save()
        await sio.emit(
            "notification_read",
            {"id": notif_id},
            room=f"user_{notif.user_id}"
        )
    except Notification.DoesNotExist:
        pass


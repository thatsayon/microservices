import socketio

# Use Redis as message queue for cross-process communication
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    client_manager=socketio.AsyncRedisManager("redis://redis:6379/0")
)


@sio.event
async def connect(sid, environ, auth):
    user_id = auth.get("user_id") if auth else None
    if user_id:
        await sio.save_session(sid, {"user_id": user_id})
        await sio.enter_room(sid, f"user_{user_id}")
        print(f"✅ User {user_id} connected via Socket.IO (sid: {sid})")
    else:
        print("❌ Connection rejected: No user_id provided")
        return False


@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if user_id:
        print(f"❌ User {user_id} disconnected (sid: {sid})")


@sio.event
async def mark_read(sid, data):
    from .models import Notification
    from django.core.exceptions import ValidationError

    notif_id = data.get("id")
    if not notif_id:
        return {"error": "Missing notification id"}

    try:
        session = await sio.get_session(sid)
        user_id = session.get("user_id")

        # 👈 Verify ownership
        notif = await Notification.objects.aget(id=notif_id, user_id=user_id)
        notif.is_read = True
        await notif.asave()

        await sio.emit(
            "notification_read",
            {"id": str(notif_id)},
            room=f"user_{user_id}"
        )
        return {"success": True}
    except Notification.DoesNotExist:
        return {"error": "Notification not found"}
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return {"error": "Internal error"}

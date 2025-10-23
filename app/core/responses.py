from datetime import datetime

def ok(data=None, message="ok"):
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

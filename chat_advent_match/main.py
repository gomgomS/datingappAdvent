from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Database connection
mainDB = "datingapp"
mainDB_string = "mongodb://127.0.0.1:27017/" + mainDB
client = MongoClient(mainDB_string)
db = client[mainDB]
db_matches = db["db_matches"]
db_users = db["db_users"]
db_chat = db["db_chat"]

rooms = {}

@app.route("/")
def home():
    return render_template("room.html")

@app.route("/chat")
def chat():
    match_id = request.args.get("match_id")
    sender_id = request.args.get("sender")

    if not match_id or not sender_id:
        return "Error: match_id and sender are required", 400

    match = db_matches.find_one({"match_id": match_id})
    if not match:
        return "Error: match not found", 404

    if sender_id == match["user_id_1"]:
        receiver_id = match["user_id_2"]
    elif sender_id == match["user_id_2"]:
        receiver_id = match["user_id_1"]
    else:
        return "Error: sender is not part of this match", 400

    sender = db_users.find_one({"user_id": sender_id})
    if not sender:
        return "Error: sender user not found", 404

    receiver = db_users.find_one({"user_id": receiver_id})
    if not receiver:
        return "Error: receiver user not found", 404

    # Fetch previous messages
    chat_messages = list(db_chat.find({"match_id": match_id}).sort("timestamp", 1))  # Sort by timestamp (oldest first)
    
    # Convert MongoDB ObjectId to string & format timestamps
    for msg in chat_messages:
        msg["_id"] = str(msg["_id"])
        msg["timestamp"] = msg["timestamp"] if isinstance(msg["timestamp"], str) else msg["timestamp"].isoformat()

    return render_template(
        "room.html",
        match_id=match_id,
        sender=sender_id,
        receiver=receiver_id,
        sender_name=sender["name"],
        sender_username=sender["username"],
        receiver_name=receiver["name"],
        chat_messages=chat_messages  # Send chat history to template
    )
    
@socketio.on("join")
def handle_join(data):
    room = data["room"]
    join_room(room)
    print(f"User joined room: {room}")

@socketio.on("message")
def handle_message(data):
    room = data["room"]
    message = data["message"]
    sender = data["sender"]
    match_id = data.get("match_id", "")

    match = db_matches.find_one({"match_id": match_id})
    if not match:
        return

    if sender == match["user_id_1"]:
        receiver = match["user_id_2"]
    elif sender == match["user_id_2"]:
        receiver = match["user_id_1"]
    else:
        return

    message_data = {
        "message": message,
        "sender_user_id": sender,
        "timestamp": datetime.utcnow().isoformat(),
        "match_id": match_id
    }

    db_chat.insert_one({
        **message_data,
        "chat_id": str(ObjectId()),
        "receiver_user_id": receiver,
        "type": "text",
        "is_read": False,
        "is_deleted": False,
    })

    # Gunakan `emit()` dengan `room`
    emit("message", message_data, room=room)


if __name__ == "__main__":
    socketio.run(app, debug=True)

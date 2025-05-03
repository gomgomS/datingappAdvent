from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, send, emit
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
main_url="http://0.0.0.0:50011/chat"
chat_dispatch_url="http://0.0.0.0:50013"

# Room dictionary to keep track of messages in memory
room_messages = {}

@app.route("/")
def home():
    return render_template("room.html")

@app.route("/chat", methods=["POST"])
def chat():
    # match_id = request.args.get("match_id")
    # sender_id = request.args.get("sender")
    match_id = request.form.get("match_id")
    sender_id = request.form.get("sender")

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

    # Fetch previous messages from MongoDB
    chat_messages = list(db_chat.find({"match_id": match_id}).sort("timestamp", 1))

    # Convert MongoDB ObjectId to string & format timestamps
    for msg in chat_messages:
        msg["_id"] = str(msg["_id"])
        msg["timestamp"] = msg["timestamp"] if isinstance(msg["timestamp"], str) else msg["timestamp"].isoformat()

    # Store messages in memory for quick access
    room_messages[match_id] = chat_messages

    # Mark unread messages as read
    db_chat.update_many(
        {"match_id": match_id, "receiver_user_id": sender_id, "is_read": False},
        {"$set": {"is_read": True}}
    )

    # Notify sender that messages have been read
    socketio.emit("messages_read", {"match_id": match_id, "receiver_id": sender_id}, room=match_id)

    last_message = db_chat.find_one({"match_id": match_id}, sort=[("sequence", -1)])
    last_sequence = last_message["sequence"] if last_message else 0
    latest_sequence = last_sequence

    return render_template(
        "room.html",
        match_id=match_id,
        sender=sender_id,
        receiver=receiver_id,
        sender_name=sender["name"],
        sender_username=sender["username"],
        receiver_name=receiver["name"],
        main_url=main_url,
        chat_messages=chat_messages,
        latest_sequence=latest_sequence
    )

@socketio.on("join")
def handle_join(data):
    room = data["room"]
    join_room(room)

    # Fetch messages from database instead of memory
    chat_messages = list(db_chat.find({"match_id": room}).sort("timestamp", 1))

    # Convert MongoDB ObjectId to string & format timestamps
    for msg in chat_messages:
        msg["_id"] = str(msg["_id"])
        msg["timestamp"] = msg["timestamp"] if isinstance(msg["timestamp"], str) else msg["timestamp"].isoformat()

    # Send messages to the user
    emit("load_previous_messages", chat_messages, room=room)

    print(f"User joined room: {room} and messages were loaded from database.")

@socketio.on("chat_opened")
def handle_chat_opened(data):
    """Mark messages as read when the opponent opens the chat"""
    match_id = data.get("match_id")
    receiver_id = data.get("receiver_id")  # The user who just opened the chat

    # Mark messages as read in the database
    db_chat.update_many(
        {"match_id": match_id, "receiver_user_id": receiver_id, "is_read": False},
        {"$set": {"is_read": True}}
    )

    # Notify the sender that their messages are now read
    emit("messages_read", {"match_id": match_id, "receiver_id": receiver_id}, room=match_id)

    print(f"Messages marked as read for match {match_id} by {receiver_id}")

@socketio.on("message")
def handle_message(data):
    room = data["room"]
    message = data["message"]
    sender = data["sender"]
    match_id = data.get("match_id", "")
    sequence = data.get("sequence", 1)

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
        "match_id": match_id,
        "sequence": sequence
    }

    db_chat.insert_one({
        **message_data,
        "chat_id": str(ObjectId()),
        "receiver_user_id": receiver,
        "type": "text",
        "is_read": False,
        "is_deleted": False,
    })

    # Kirim pesan ke semua user di room (termasuk pengirim)
    emit("message", message_data, room=room)

@socketio.on("leave")
def handle_leave(data):
    room = data["room"]
    sender = data["sender"]

    # Remove the room messages from memory
    if room in room_messages:
        del room_messages[room]    

    # Notify others in the room
    # emit("user_left", {"sender": sender, "message": "has left the chat."}, room=room)

    print(f"User {sender} left room: {room} and messages were cleared.")

if __name__ == "__main__":
    # socketio.run(app, debug=True)
    socketio.run(app, debug=True, port=50013)
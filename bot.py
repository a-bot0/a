
import websockets
import threading
import json
import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

ID = "id"
NAME = "name"
USERNAME = "username"
PASSWORD = "password"
ROOM = "room"
TYPE = "type"
HANDLER = "handler"
ALLOWED_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"
SOCKET_URL = "wss://chatp.net:5333/server"

MSG_BODY = "body"
MSG_FROM = "from"
MSG_TO = "to"
MSG_TYPE_TXT = "text"
HANDLER_LOGIN = "login"
HANDLER_ROOM_MESSAGE = "room_message"
HANDLER_ROOM_JOIN = "room_join"
HANDLER_ROOM_LEAVE = "room_leave"
HANDLER_ROOM_EVENT = "room_event"


async def on_message(ws, data):
    msg = data[MSG_BODY]
    frm = data[MSG_FROM]
    room = data[ROOM]


async def login(websocket, bot_id, bot_pwd):
    login_data = {
        HANDLER: HANDLER_LOGIN,
        ID: str(hash(bot_id)),
        USERNAME: bot_id,
        PASSWORD: bot_pwd
    }
    await websocket.send(json.dumps(login_data))


async def leave_group(ws, room):
    jsonbody = {
        HANDLER: HANDLER_ROOM_LEAVE,
        NAME: room,
        ID: gen_random_str(20)
    }
    await ws.send(json.dumps(jsonbody, ensure_ascii=False))


async def send_group_msg(ws, room, msg):
    jsonbody = {
        HANDLER: HANDLER_ROOM_MESSAGE,
        ID: gen_random_str(20),
        ROOM: room,
        TYPE: MSG_TYPE_TXT,
        MSG_BODY: msg
    }
    await ws.send(json.dumps(jsonbody))


async def join_group(websocket, room_name):
    join_data = {
        HANDLER: HANDLER_ROOM_JOIN,
        ID: str(hash(room_name)),
        NAME: room_name
    }
    await websocket.send(json.dumps(join_data))


def gen_random_str(length):
    return ''.join(random.choice(ALLOWED_CHARS) for i in range(length))


async def account_session(bot_id, bot_pwd, room_name):
    try:
        async with websockets.connect(SOCKET_URL, ssl=True) as websocket:
            await login(websocket, bot_id, bot_pwd)
            print(f"Login successful for bot ID: {bot_id}")
            await join_group(websocket, room_name)

            while True:
                try:
                    data = await websocket.recv()
                    data = json.loads(data)
                    handler = data.get(HANDLER)
                    if handler == HANDLER_ROOM_EVENT and data[
                            TYPE] == MSG_TYPE_TXT:
                        await on_message(websocket, data)
                except Exception as e:
                    print("Error receiving message:", e)
                    break
    except Exception as e:
        print("Error connecting websocket:", e)


def start_bot_session(bot_id, bot_pwd, room_name):
    asyncio.new_event_loop().run_until_complete(
        account_session(bot_id, bot_pwd, room_name))


def start_bots(bots_info):
    for bot in bots_info:
        t = threading.Thread(target=start_bot_session,
                             args=(bot['id'], bot['pwd'], bot['room']))
        t.start()
        time.sleep(7)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_bots', methods=['POST'])
def start_bots_endpoint():
    try:
        bots_info = request.json.get("bots_info", [])
        room_name = request.json.get("room_name", "نبض")
        for bot in bots_info:
            bot["room"] = room_name
        threading.Thread(target=start_bots, args=(bots_info, )).start()
        return jsonify({"status": "started"}), 200
    except Exception as e:
        print("Error in /start_bots endpoint:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
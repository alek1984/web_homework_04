import json
import os
import threading
import socket
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory

# Налаштування Flask
app = Flask(__name__, template_folder='templates', static_folder='static')
STORAGE_DIR = "storage"
DATA_FILE = os.path.join(STORAGE_DIR, "data.json")
PORT_HTTP = 3000
PORT_SOCKET = 5000

# Функція для збереження повідомлень у JSON
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def save_message(username, message):
    timestamp = str(datetime.now())
    data = {}
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    
    data[timestamp] = {"username": username, "message": message}
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# HTTP маршрутизація
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/message', methods=["GET", "POST"])
def message():
    if request.method == "POST":
        username = request.form.get("username")
        message = request.form.get("message")
        
        if username and message:
            send_message_to_socket(username, message)
            return "Повідомлення надіслано!", 200
        else:
            return "Помилка! Всі поля обов'язкові!", 400
    
    return render_template("message.html")

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html"), 404

# Функція для надсилання повідомлення на socket-сервер
def send_message_to_socket(username, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', PORT_SOCKET)
    message_data = json.dumps({"username": username, "message": message}).encode("utf-8")
    sock.sendto(message_data, server_address)
    sock.close()

# Socket сервер

def socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", PORT_SOCKET))
    print(f"Socket сервер запущено на порту {PORT_SOCKET}")
    
    while True:
        data, addr = sock.recvfrom(1024)
        message = json.loads(data.decode("utf-8"))
        save_message(message["username"], message["message"])

# Запуск серверів у потоках
if __name__ == "__main__":
    socket_thread = threading.Thread(target=socket_server, daemon=True)
    socket_thread.start()
    print(f"HTTP сервер запущено на порту {PORT_HTTP}")
    app.run(port=PORT_HTTP, debug=True)

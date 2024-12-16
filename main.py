import os
import json
import socket
import threading
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import pymongo

HOST = '0.0.0.0'
HTTP_PORT = 3000
SOCKET_PORT = 5000

# MongoDB конфігурація
MONGO_HOST = "mongodb"  # Для Docker Compose
MONGO_PORT = 27017
DB_NAME = "messages_db"
COLLECTION_NAME = "messages"

# Шляхи до папок
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "project", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "project", "templates")


# HTTP-сервер
class CustomHandler(SimpleHTTPRequestHandler):
    def send_static_file(self, file_name):
        """Обробка статичних файлів (CSS, зображення)"""
        file_path = os.path.join(STATIC_DIR, file_name)
        if os.path.exists(file_path):
            self.send_response(200)
            if file_path.endswith(".css"):
                self.send_header("Content-Type", "text/css")
            elif file_path.endswith(".png"):
                self.send_header("Content-Type", "image/png")
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"Static file {file_name} not found")

    def send_template(self, template_name):
        """Обробка HTML-шаблонів"""
        file_path = os.path.join(TEMPLATES_DIR, template_name)
        if os.path.exists(file_path):
            self.send_response(200)
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"Template {template_name} not found")

    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/index.html":
                # Головна сторінка
                self.send_template("index.html")
            elif self.path == "/message.html":
                # Сторінка повідомлень
                self.send_template("message.html")
            elif self.path.startswith("/static/"):
                # Обробка статичних файлів
                file_name = self.path.split("/static/")[-1]
                self.send_static_file(file_name)
            else:
                # Невідомий маршрут
                self.send_template("error.html")
        except Exception as e:
            print(f"Помилка обробки GET-запиту: {e}")
            self.send_error(500, "Internal Server Error")

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                data = dict(x.split('=') for x in post_data.split('&'))
                send_data_to_socket(data)  # Відправка даних до Socket-сервера
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Message received")
            except Exception as e:
                print(f"Помилка обробки POST-запиту: {e}")
                self.send_error(500, "Internal Server Error")
        else:
            self.send_error(404)


# Запуск HTTP-сервера
def run_http_server():
    server = HTTPServer((HOST, HTTP_PORT), CustomHandler)
    print(f"HTTP сервер запущено на {HTTP_PORT} порту")
    server.serve_forever()


# Socket-сервер
def run_socket_server():
    try:
        client = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((HOST, SOCKET_PORT))
        sock.listen(5)
        print(f"Socket сервер запущено на {SOCKET_PORT} порту")

        while True:
            conn, addr = sock.accept()
            try:
                data = conn.recv(1024).decode("utf-8")
                message = json.loads(data)
                message["date"] = str(datetime.now())
                collection.insert_one(message)
                print(f"Отримано та збережено: {message}")
            except Exception as e:
                print(f"Помилка обробки Socket: {e}")
            finally:
                conn.close()
    except Exception as e:
        print(f"Помилка підключення до MongoDB: {e}")


# Відправка даних у Socket-сервер
def send_data_to_socket(data):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, SOCKET_PORT))
        sock.sendall(json.dumps(data).encode("utf-8"))
    except Exception as e:
        print(f"Помилка відправки даних у Socket: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    threading.Thread(target=run_http_server).start()
    threading.Thread(target=run_socket_server).start()
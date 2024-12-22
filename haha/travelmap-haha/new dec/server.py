import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer


def run_server():
    handler = SimpleHTTPRequestHandler
    server = HTTPServer(("localhost", 8000), handler)
    print("HTTP сервер запущен на http://localhost:8000")
    server.serve_forever()


def start_server():
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

import socket

HOST = "127.0.0.1"
PORT = 5003

with open("index.html", "r", encoding="utf-8") as file:
    html = file.read().encode("utf-8")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Сервер запущен: http://{HOST}:{PORT}")

while True:
    client_socket, client_address = server_socket.accept()
    client_socket.settimeout(2)
    try:
        request = client_socket.recv(4096)
    except (socket.timeout, ConnectionError):
        client_socket.close()
        continue

    if request:
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(html)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )

        try:
            client_socket.sendall(headers.encode("utf-8") + html)
        except (socket.timeout, ConnectionError):
            print("Браузер закрыл соединение или не принял ответ.")

    client_socket.close()

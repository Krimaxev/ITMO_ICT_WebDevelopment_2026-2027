import socket

HOST = "127.0.0.1"
PORT = 5001

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"TCP server started on {HOST}:{PORT}")

client_socket, client_address = server_socket.accept()
print(f"Client connected: {client_address}")

data = client_socket.recv(1024).decode()

a, h = map(float, data.split())

S = a * h

client_socket.send(str(S).encode())

client_socket.close()
server_socket.close()
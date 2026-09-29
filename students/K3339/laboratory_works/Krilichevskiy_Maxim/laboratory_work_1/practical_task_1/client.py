import socket

HOST = "127.0.0.1"
PORT = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
message = "Hello, server"
client_socket.sendto(message.encode(), (HOST, PORT))
data, server_address = client_socket.recvfrom(1024)

print(f"Server says: {data.decode()}")

client_socket.close()
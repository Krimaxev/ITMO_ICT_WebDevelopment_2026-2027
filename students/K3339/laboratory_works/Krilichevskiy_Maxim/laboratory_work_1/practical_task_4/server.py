import socket
import threading

HOST = "127.0.0.1"
PORT = 5004

clients = []
lock = threading.Lock()


def handle_client(client):
    try:
        with client.makefile("r", encoding="utf-8") as messages:
            for message in messages:
                with lock:
                    for other in clients:
                        if other != client:
                            try:
                                other.sendall(message.encode("utf-8"))
                            except OSError:
                                pass
    except (OSError, UnicodeError):
        pass
    finally:
        with lock:
            clients.remove(client)
        client.close()


def main():
    threads = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"Чат запущен на {HOST}:{PORT}", flush=True)

        try:
            while True:
                client, address = server.accept()
                with lock:
                    clients.append(client)
                print("Участник подключился", flush=True)
                thread = threading.Thread(target=handle_client, args=(client,))
                thread.start()
                threads.append(thread)
        except KeyboardInterrupt:
            print("\nСервер остановлен.")
        finally:
        
            with lock:
                connected = clients.copy()
            for client in connected:
                try:
                    client.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            for thread in threads:
                thread.join()


if __name__ == "__main__":
    main()

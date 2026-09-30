import socket
import threading

HOST = "127.0.0.1"
PORT = 5004
closed = threading.Event()  


def receive_messages(client):
    try:
        with client.makefile("r", encoding="utf-8") as messages:
            for message in messages:
                print(message, end="", flush=True)
    except (OSError, UnicodeError):
        pass
    finally:
        closed.set()
        print("Соединение закрыто. Нажмите Enter для выхода.", flush=True)


name = input("Ваше имя: ").strip()
if not name:
    name = "Гость"

thread = None
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    try:
        client.connect((HOST, PORT))
        thread = threading.Thread(target=receive_messages, args=(client,))
        thread.start()
        print("Введите сообщение или /exit для выхода.", flush=True)

        while not closed.is_set():
            text = input()
            if text == "/exit" or closed.is_set():
                break
            if text.strip():
                message = f"{name}: {text}\n"
                client.sendall(message.encode("utf-8"))
    except (EOFError, KeyboardInterrupt):
        print("\nВыход из чата.")
    except OSError:
        print("Нет связи с сервером. Проверьте, запущен ли он.")
    finally:
        try:
            client.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        if thread is not None:
            thread.join()

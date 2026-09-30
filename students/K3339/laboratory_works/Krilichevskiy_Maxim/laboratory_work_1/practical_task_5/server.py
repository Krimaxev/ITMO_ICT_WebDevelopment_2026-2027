import socket
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


class MyHTTPServer:
    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.name = name
        self.grades = {}
        self.page_file = Path(__file__).with_name("index.html")

    def serve_forever(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(5)
            print(f"Сервер запущен: http://{self.host}:{self.port}", flush=True)
            while True:
                client, address = server.accept()
                self.serve_client(client)

    def serve_client(self, client):
        with client:
            client.settimeout(2)
            try:
                request = self.parse_request(client)
                if request is None:
                    return
                status, text, headers = self.handle_request(request)
                self.send_response(client, status, text, headers)
            except (ValueError, UnicodeError):
                try:
                    self.send_response(client, "400 Bad Request", "Неверный запрос", {})
                except OSError:
                    pass
            except OSError:
                pass  # Клиент отключился или не отправил запрос вовремя.

    def parse_request(self, client):
        with client.makefile("rb") as reader:
            line = reader.readline(65537)
            if not line:
                return None
            if len(line) > 65536:
                raise ValueError("Слишком длинный запрос")
            method, target, version = line.decode("iso-8859-1").split()
            if version not in ["HTTP/1.0", "HTTP/1.1"]:
                raise ValueError("Неверная версия HTTP")

            url = urlsplit(target)
            headers = self.parse_headers(reader)
            if "transfer-encoding" in headers:
                raise ValueError("Используйте Content-Length")
            length = int(headers.get("content-length", "0"))
            if length < 0 or length > 65536:
                raise ValueError("Неверный размер тела")
            body = reader.read(length)
            if len(body) != length:
                raise ValueError("Тело запроса получено не полностью")

        return {
            "method": method,
            "path": url.path,
            "query": parse_qs(url.query),
            "headers": headers,
            "body": body.decode("utf-8"),
        }

    def parse_headers(self, reader):
        headers = {}
        total = 0
        while True:
            line = reader.readline(65537)
            total += len(line)
            if not line or total > 65536:
                raise ValueError("Неверные заголовки")
            if line == b"\r\n":
                return headers
            name, value = line.decode("iso-8859-1").split(":", 1)
            headers[name.strip().lower()] = value.strip()

    def handle_request(self, request):
        if request["path"] != "/":
            return "404 Not Found", "Страница не найдена", {}

        if request["method"] == "GET":
            rows = ""
            for subject, grades in self.grades.items():
                grades_text = ", ".join(grades)
                rows += f"<tr><td>{escape(subject)}</td><td>{grades_text}</td></tr>"
            if not self.grades:
                rows = '<tr><td colspan="2">Оценок пока нет.</td></tr>'
            page = self.page_file.read_text(encoding="utf-8")
            return "200 OK", page.replace("<!-- GRADES -->", rows), {}

        if request["method"] == "POST":
            form = request["query"].copy()
            form.update(parse_qs(request["body"], keep_blank_values=True))
            subject = form.get("subject", [""])[0].strip()
            grade = form.get("grade", [""])[0]
            if not subject or grade not in ["2", "3", "4", "5"]:
                return "400 Bad Request", "Укажите дисциплину и оценку от 2 до 5.", {}
            if subject not in self.grades:
                self.grades[subject] = []
            self.grades[subject].append(grade)
            return "303 See Other", "", {"Location": "/"}

        return "405 Method Not Allowed", "Разрешены GET и POST", {"Allow": "GET, POST"}

    def send_response(self, client, status, text, extra_headers):
        body = text.encode("utf-8")
        headers = {
            "Server": self.name,
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": str(len(body)),
            "Connection": "close",
        }
        headers.update(extra_headers)
        response = f"HTTP/1.1 {status}\r\n"
        for name, value in headers.items():
            response += f"{name}: {value}\r\n"
        response += "\r\n"
        client.sendall(response.encode("iso-8859-1") + body)


if __name__ == "__main__":
    server = MyHTTPServer("127.0.0.1", 5005, "GradesServer")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")

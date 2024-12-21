from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from requests import get, put
import urllib.parse
import json

YANDEX_TOKEN = "y0_AgAAAAAjAgqUAADLWwAAAAEdJgICAACVo7nXuyRAxLfEJ8GH2GDlDV8h4w"  # Ваш OAuth-токен

def run(handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, handler_class)
    try:
        print("Server running on port 8000...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Проверка, существует ли файл на Яндекс.Диске
        def is_file_uploaded(fname):
            ya_path = f"Backup/{urllib.parse.quote(fname)}"
            resp = get(f"https://cloud-api.yandex.net/v1/disk/resources?path={ya_path}",
                       headers={"Authorization": f"OAuth {YANDEX_TOKEN}"})
            return resp.status_code == 200  # Если файл существует, вернётся 200

        # Генерация HTML для файлов
        def fname2html(fname):
            if is_file_uploaded(fname):
                # Фон зелёный для загруженных файлов
                return f"""
                    <li style="background-color: rgba(0, 200, 0, 0.25);"
                        onclick="fetch('/upload', {{'method': 'POST', 'body': '{fname}'}})">
                        {fname}
                    </li>
                """
            else:
                # Обычный фон для незагруженных файлов
                return f"""
                    <li onclick="fetch('/upload', {{'method': 'POST', 'body': '{fname}'}})">
                        {fname}
                    </li>
                """

        # Генерируем HTML
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        files_html = "\n".join(map(fname2html, os.listdir("pdfs")))
        self.wfile.write(f"""
            <html>
                <head>
                </head>
                <body>
                    <ul>
                      {files_html}
                    </ul>
                </body>
            </html>
        """.encode())

    def do_POST(self):
        # Получение имени файла из POST-запроса
        content_len = int(self.headers.get('Content-Length'))
        fname = self.rfile.read(content_len).decode("utf-8")
        local_path = f"pdfs/{fname}"
        ya_path = f"Backup/{urllib.parse.quote(fname)}"

        # Загружаем файл на Яндекс.Диск
        resp = get(f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={ya_path}",
                   headers={"Authorization": f"OAuth {YANDEX_TOKEN}"})
        if resp.status_code != 200:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Failed to get upload URL")
            return

        upload_url = json.loads(resp.text).get("href")
        with open(local_path, 'rb') as f:
            upload_resp = put(upload_url, files={'file': (fname, f)})
        if upload_resp.status_code == 201:
            print(f"File {fname} uploaded successfully.")

        # Отправка ответа клиенту
        self.send_response(200)
        self.end_headers()


run(handler_class=HttpGetHandler)
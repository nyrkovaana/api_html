from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import os
from requests import get, put
import urllib.parse
import json


def run(handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        def fname2html(fname):
            return f"""
                <li onclick="fetch('/upload', {{'method': 'POST', 'body': '{fname}'}})">
                    {fname}
                </li>
            """

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("""
            <html>
                <head>
                </head>
                <body>
                    <ul>
                      {files}
                    </ul>
                </body>
            </html>
        """.format(files="\n".join(map(fname2html, os.listdir("pdfs")))).encode())

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        fname = self.rfile.read(content_len).decode("utf-8")
        local_path = f"pdfs/{fname}"
        ya_path = f"Backup/{urllib.parse.quote(fname)}"
        resp = get(f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={ya_path}",
                   headers={"Authorization": "OAuth yJgICAACVo7nXuyRAxLfEJ8GH2GDlDV8h4w"})
        print(resp.text)
        upload_url = json.loads(resp.text)["href"]
        print("_____")
        print(upload_url)
        resp = put(upload_url, files={'file': (fname, open(local_path, 'rb'))})
        print("_____")
        print(resp.status_code)
        self.send_response(200)
        self.end_headers()


run(handler_class=HttpGetHandler)
import http.server
from socketserver import ThreadingMixIn
import logging
from PathManager import PathsManager
from DbManager import DB
import json


def file_to_bit(file_path):
    with open(file_path, 'rb') as f:  # Open file in binary mode
        byte_data = f.read()  # Read the entire file content in bytes
        # Convert each byte to a bit string and join them together
    return byte_data

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        """
        This method initializes a new EnigmaHandler-Object and uses the params request, client_address, server.
        It also calls super().__init__() and creates a Handler Logger.
        :param request:
        :param client_address:
        :param server:
        """
        # Setup logger
        self._logger = logging.getLogger("Handle Logger")
        self._logger.setLevel(logging.INFO)

        if not self._logger.handlers:
            # This stops multiple useless log entries
            fh = logging.FileHandler(
                PathsManager().getPath("logs")
            )
            fh.setLevel(logging.INFO)

            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)

            self._logger.addHandler(fh)

        self._logger.info(f"Server has connected with {client_address}")
        # calling super().__init__() to make sure everything works fine
        super().__init__(request, client_address, server)

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(file_to_bit(PathsManager().getPath("static", "pre_game", "creatUser")))
            return

        if self.path.startswith("/static"):
            path: list = self.path.split("/")
            path: list = [sub for sub in path if sub != ""]
            if path[1] == "css":
                self.send_response(200)
                self.send_header("Content-type", "text/css")
                self.end_headers()
                self.wfile.write(file_to_bit(PathsManager().getPath(*path)))
                return
            elif path[1] == "img":
                img = file_to_bit(PathsManager().getPath(*path))
                self.send_response(200)
                self.send_header("Content-type", "image/jpg")
                self.send_header("Content-Length", len(img))
                self.end_headers()
                self.wfile.write(img)
            elif path[1] == "fonts":
                font = file_to_bit(PathsManager().getPath(*path))
                self.send_response(200)
                self.send_header("Content-type", "font/ttf")
                self.send_header("Content-Length", len(font))
                self.end_headers()
                self.wfile.write(font)




    def do_POST(self):
        path: list = self.path.split("/")
        path: list = [sub for sub in path if sub != ""]
        if path[0] == "teams":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            post_data = str(post_data)
            username: str = post_data[post_data.find("=")+1:-1]
            DB(PathsManager().getPath("db")).createUser(username, self.client_address[0])
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(file_to_bit(PathsManager().getPath("static", "pre_game", "teams")))

        elif path[0] == "api":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            post_data = json.loads(str(post_data)[2:-1])
            if post_data["message"] == "username":
                user: dict = DB(PathsManager().getPath("db")).getUser(self.client_address[0])
                data: dict = {"username": user["name"]}
                response_json = json.dumps(data)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(response_json.encode("utf-8"))



def run_server():
    server_address = ('', 80)
    httpd = ThreadedHTTPServer(server_address, SimpleHTTPRequestHandler)

    # SSL-Kontext konfigurieren
    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    # SSL auf den Server-Socket anwenden
    # httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    print("HTTP-Server läuft auf http://localhost:80")
    httpd.serve_forever()


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt as err:
        print("Server closed")
    except Exception as ex:
        print(ex)

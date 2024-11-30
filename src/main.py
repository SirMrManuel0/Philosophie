import http.server
import urllib.parse
from socketserver import ThreadingMixIn
import logging
from PathManager import PathsManager
from DbManager import DB
import json
import hashlib

ADDR: str = "127.0.0.1"

def file_to_bit(file_path):
    if file_path.endswith(".html"):
        with open(file_path, 'r') as fs:
            file: str = fs.read()
        file.replace("ADDRESS", ADDR)
        return file.encode()
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
        Base: DB = DB(PathsManager().getPath("db"))
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(file_to_bit(PathsManager().getPath("static", "pre_game", "creatUser")))
            return
        if self.path == "/teams" and not Base.hasGameStarted():
            Users: set = set(Base.getUsers().keys())
            if self.client_address[0] in Users:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(file_to_bit(PathsManager().getPath("static", "pre_game", "teams")))
            else:
                self.send_response(302)
                self.send_header('Location', f'http://{ADDR}')
                self.end_headers()
        if self.path == "/landingPage" and not Base.hasGameStarted():
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(file_to_bit(PathsManager().getPath("static", "pre_game", "landingPage")))
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
                if path[-1][:-3] == "jpg":
                    self.send_header("Content-type", "image/jpg")
                elif path[-1][:-3] == "png":
                    self.send_header("Content-type", "image/png")
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
            username: str = post_data[post_data.find("=") + 1:-1]
            username_hash = hashlib.sha256(username.encode())
            username_hash = username_hash.hexdigest()
            if username_hash == "5823d1bc9416c2996bc9572da20cc9efa617fc036181e2d42c7e8b198519e7fa":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(file_to_bit(PathsManager().getPath("static", "admin", "lander")))
            elif not DB(PathsManager().getPath("db")).hasGameStarted():
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
            elif post_data["message"] == "teams":
                teams: list = DB(PathsManager().getPath("db")).getTeams()
                data: dict = {"teams": teams}
                response_json = json.dumps(data)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(response_json.encode("utf-8"))
        elif path[0] == "team_create":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
            form_data = {key: values[0] for key, values in parsed_data.items()}
            Base: DB = DB(PathsManager().getPath("db"))
            teamId: int = Base.createTeam(form_data["Teamname"], form_data["Teamfarbe"],
                                          form_data["gebiet"], self.client_address[0])
            Base.assignTeam(self.client_address[0], teamId)
            self.send_response(302)
            self.send_header('Location', f'http://{ADDR}/teams')
            self.end_headers()


def run_server():
    server_address = (ADDR, 80)
    httpd = ThreadedHTTPServer(server_address, SimpleHTTPRequestHandler)

    # SSL-Kontext konfigurieren
    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    # SSL auf den Server-Socket anwenden
    # httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    print(f"HTTP-Server läuft auf http://{ADDR}:80")
    httpd.serve_forever()


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt as err:
        print("Server closed")
    except Exception as ex:
        print(ex)

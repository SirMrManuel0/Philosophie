import http.server
import os.path
import urllib.parse
from socketserver import ThreadingMixIn
import logging
from PathManager import PathsManager
from DbManager import DB
import json
import hashlib
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("ip", help="Server IP")

ADDR: str = parser.parse_args().ip





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
                PathsManager().get_path("logs")
            )
            fh.setLevel(logging.INFO)

            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)

            self._logger.addHandler(fh)

        self._logger.info(f"Server has connected with {client_address}")
        # calling super().__init__() to make sure everything works fine
        super().__init__(request, client_address, server)

    def _file_to_bit(self, file_path):
        if file_path.endswith(".html"):
            with open(file_path, 'r', encoding="utf-8") as fs:
                file: str = fs.read()
            file = file.replace("ADDRESS", ADDR)
            return file.encode()
        with open(file_path, 'rb') as f:  # Open file in binary mode
            byte_data = f.read()  # Read the entire file content in bytes
            # Convert each byte to a bit string and join them together
        return byte_data

    def _transfer_to(self, address: str) -> None:
        self.send_response(302)
        if address == "":
            self.send_header('Location', f'http://{ADDR}')
        else:
            self.send_header('Location', f'http://{ADDR}/{address}')
        self.end_headers()
        self._logger.info(f"Transferred {self.client_address} to http://{ADDR}/{address}")

    def _send_file(self, *path) -> None:
        self.send_response(200)
        file = self._file_to_bit(PathsManager().get_path(*path))
        if "css" in path:
            self.send_header("Content-type", "text/css")
        elif path[-1][:-3] == "jpg":
            self.send_header("Content-type", "image/jpg")
            self.send_header("Content-Length", len(file))
        elif path[-1][:-3] == "png":
            self.send_header("Content-type", "image/png")
            self.send_header("Content-Length", len(file))
        elif "fonts" in path:
            self.send_header("Content-type", "font/ttf")
            self.send_header("Content-Length", len(file))
        else:
            self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(file)
        self._logger.info(f"Send file {path} to {self.client_address}")

    def _send_json(self, data: dict) -> None:
        response_json = json.dumps(data)
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(response_json.encode("utf-8"))
        self._logger.info(f"Send JSON to client {self.client_address}")

    def do_GET(self):
        self._logger.info(f"Received GET Request from {self.client_address}.")
        Base: DB = DB(PathsManager().get_path("db"))
        if self.path == "/":
            self._send_file("static", "pre_game", "creatUser")
            return
        if (not Base.is_user(self.client_address[0]) and not Base.has_game_started()
                and not self.path.startswith("/static")):
            self._transfer_to("")
            return
        if self.path == "/gameStarted":
            self._logger.info(f"Received GET Request from {self.client_address}. The client was sent to game started.")
            self._send_file("static", "game", "gameStarted")
            return
        if self.path == "/teams" and not Base.has_game_started():
            self._logger.info(f"Received GET request from {self.client_address} for teams. The game has yet to start.")
            if Base.is_user(self.client_address[0]):
                self._send_file("static", "pre_game", "teams")
                return
            else:
                self._transfer_to("")
                return
        elif self.path == "/teams":
            self._transfer_to("gameStarted")
            return
        elif self.path == "/landingPage" and not Base.has_game_started() and Base.is_in_team(self.client_address[0]):
            self._logger.info(f"Received GET request from {self.client_address} for landingPage. The game has yet to "
                              f"start. User is allowed.")
            self._send_file("static", "pre_game", "landingPage")
            return
        elif self.path == "/landingPage" and not Base.has_game_started():
            self._logger.info(f"Received GET request from {self.client_address} for teams. The user is in no team.")
            if Base.is_user(self.client_address[0]):
                self._logger.info(
                    f"Received GET request from {self.client_address} for teams. Client is a User. Client is in no team.")
                self._transfer_to("teams")
                return
            self._transfer_to("")
            return
        elif self.path == "/landingPage":
            self._transfer_to("gameStarted")
            return

        if self.path.startswith("/static"):
            path: list = self.path.split("/")
            path: list = [sub for sub in path if sub != ""]
            if path[1] == "css":
                self._send_file(*path)
                return
            elif path[1] == "img":
                self._send_file(*path)
            elif path[1] == "fonts":
                self._send_file(*path)

    def do_POST(self):
        self._logger.info(f"Received POST Request from {self.client_address}.")
        path: list = self.path.split("/")
        path: list = [sub for sub in path if sub != ""]
        if path[0] == "teams":
            self._logger.info(f"Received POST Request from {self.client_address} for teams.")
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            post_data = str(post_data)
            username: str = post_data[post_data.find("=") + 1:-1]
            username_hash = hashlib.sha256(username.encode())
            username_hash = username_hash.hexdigest()
            if username_hash == "5823d1bc9416c2996bc9572da20cc9efa617fc036181e2d42c7e8b198519e7fa":
                self._logger.info(f"Received POST Request from {self.client_address}. User is Admin")
                self._send_file("static", "admin", "lander")
                return
            elif not DB(PathsManager().get_path("db")).has_game_started():
                self._logger.info(f"Received POST Request from {self.client_address}. User is normal.")
                DB(PathsManager().get_path("db")).create_user(username, self.client_address[0])
                self._send_file("static", "pre_game", "teams")
                return
        elif path[0] == "assign_team":
            self._logger.info(f"Received POST Request from {self.client_address}. User requests team assigning.")
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
            form_data = {key: values[0] for key, values in parsed_data.items()}
            Base: DB = DB(PathsManager().get_path("db"))
            if Base.is_team(form_data["teamname"]):
                Base.assign_team(self.client_address[0], Base.get_team_by_name(form_data["teamname"]))
                self._logger.info(f"{self.client_address[0]} is assign to team {form_data["teamname"]}")
                self._transfer_to("landingPage")
                return
        elif path[0] == "api":
            self._logger.info(f"Received POST Request from {self.client_address} for api.")
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            post_data = json.loads(str(post_data)[2:-1])
            Base: DB = DB(PathsManager().get_path("db"))
            if post_data["message"] == "username":
                self._logger.info(f"Received POST Request from {self.client_address}. Username is requested.")
                user: dict = Base.get_user(self.client_address[0])
                data: dict = {"username": user["name"]}
            elif post_data["message"] == "teams":
                self._logger.info(f"Received POST Request from {self.client_address}. Teams are requested.")
                teams: list = Base.get_teams()
                data: dict = {"teams": teams}
            elif post_data["message"] == "user_country":
                self._logger.info(f"Received POST Request from {self.client_address}. User country is requested.")
                country: str = Base.get_chosen_country(self.client_address[0])
                if country == "":
                    country: str = "Frankreich"
                data: dict = {"user_country": country}
            elif post_data["message"] == "teamname":
                self._logger.info(f"Received POST Request from {self.client_address}. User Team Name is requested.")
                data: dict = {"teamname": Base.get_team_name(Base.get_team(self.client_address[0]))}
            elif post_data["message"] == "team_votes":
                self._logger.info(f"Received POST Request from {self.client_address}. User team_votes is requested.")
                data: dict = {"team_votes": Base.get_team_votes()}
            elif post_data["message"] == "check_country_team":
                self._logger.info(f"Received POST Request from {self.client_address}. check_country_team.")
                if Base.have_all_chosen_country(Base.get_team(self.client_address[0])):
                    self._transfer_to("game")
                    return
            else:
                self._logger.warning(f"Received POST Request from {self.client_address}. Unknown reason!")
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                return
            self._send_json(data)
            return

        elif path[0] == "team_create":
            self._logger.info(f"Received POST Request from {self.client_address} for team_create.")
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
            form_data = {key: values[0] for key, values in parsed_data.items()}
            Base: DB = DB(PathsManager().get_path("db"))
            teamId: int = Base.create_team(form_data["Teamname"], form_data["Teamfarbe"],
                                           form_data["gebiet"], self.client_address[0])
            self._logger.info(f"Created team {form_data["Teamname"]}{form_data["Teamfarbe"]}, {form_data["gebiet"]}"
                              f" due to {self.client_address[0]}")
            Base.assign_team(self.client_address[0], teamId)
            self._transfer_to("teams")
            return
        elif path[0] == "select_country":
            self._logger.info(f"Received POST Request from {self.client_address} for select_country.")
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
            form_data = {key: values[0] for key, values in parsed_data.items()}
            Base: DB = DB(PathsManager().get_path("db"))
            Base.set_country(self.client_address[0], form_data["country"])
            if Base.have_all_chosen_country(Base.get_team(self.client_address[0])):
                self._logger.info(f"Team {Base.get_team_name(Base.get_team(self.client_address[0]))} has decided on a country The "
                                  f"country is {Base.get_team_country(Base.get_team(self.client_address[0]))}.")
                Base.set_team_country(Base.get_team(self.client_address[0]))
                self._transfer_to("game")
                return
            self._transfer_to("landingPage")


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
    log_file: str = PathsManager().get_path("logs")
    if not os.path.isfile(log_file):
        path: str = "/".join(log_file.split("/")[:-1])
        if not os.path.isdir(path):
            os.mkdir(path)
        with open(log_file, "w") as f:
            f.write(".\n")
    try:
        run_server()
    except KeyboardInterrupt as err:
        print("Server closed")
    except Exception as ex:
        print(ex)

import http.server
import ssl
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Hallo von deinem HTTPS-Server!</h1>")
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Hallo von deinem HTTPS-Server!</h1>")

def run_server():
    server_address = ('', 4443)
    httpd = ThreadedHTTPServer(server_address, SimpleHTTPRequestHandler)

    # SSL-Kontext konfigurieren
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    # SSL auf den Server-Socket anwenden
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    print("HTTPS-Server läuft auf https://localhost:4443")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()

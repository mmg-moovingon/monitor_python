import sys
import os

# For compatibility with both Python 2 and Python 3
try:
    # Python 3 imports
    from http.server import SimpleHTTPRequestHandler
    from socketserver import TCPServer
except ImportError:
    # Python 2 imports
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from SocketServer import TCPServer

PORT = 8086
STATUS_FILE = './status.json'

class StatusRequestHandler(SimpleHTTPRequestHandler):
    """Custom handler to serve the status.json file."""

    def do_GET(self):
        """Handle GET requests and serve the status.json file."""
        if self.path == '/status':
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r') as f:
                    status_data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                # Write the JSON data to the response
                if sys.version_info[0] < 3:
                    self.wfile.write(status_data)
                else:
                    self.wfile.write(status_data.encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                error_message = "File not found."
                if sys.version_info[0] < 3:
                    self.wfile.write(error_message)
                else:
                    self.wfile.write(error_message.encode('utf-8'))
        else:
            # Handle other paths
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            error_message = "Path not found."
            if sys.version_info[0] < 3:
                self.wfile.write(error_message)
            else:
                self.wfile.write(error_message.encode('utf-8'))

def run_server(port):
    """Run the HTTP server."""
    try:
        httpd = TCPServer(("", port), StatusRequestHandler)
        print("Serving status.json on port {}".format(port))
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server.")
        httpd.shutdown()

if __name__ == "__main__":
    run_server(PORT)
#!/usr/bin/env python3

import http.server, ssl, os, sys, socket
import socketserver

def ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1)) # doesn't even have to be reachable
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

serverdir = os.path.dirname(os.path.abspath(__file__))
httpdir = serverdir + '/../web_viewer'
pem = serverdir + '/server.pem'
port = int(sys.argv[1]) if len(sys.argv) == 2 else 4343
#httpd = http.server.HTTPServer(('0.0.0.0', port), http.server.SimpleHTTPRequestHandler)
if not os.path.isfile(pem):
    os.system(f'openssl req -new -x509 -keyout {pem} -out {pem} -days 3650 -nodes -subj /C=US')
#httpd.socket = ssl.wrap_socket(httpd.socket, certfile=pem, server_side=True)
print(f'https://{ip()}:{port}/')
#httpd.serve_forever()



class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=httpdir, **kwargs)


with socketserver.TCPServer(("", port), Handler) as httpd:
    print("serving at port", port)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=pem, server_side=True)
    httpd.serve_forever()

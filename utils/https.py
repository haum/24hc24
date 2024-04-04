#!/usr/bin/env python3

import http.server
import os
import re
import random
import socket
import socketserver
import ssl
import string
import sys

from map import Map

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
mapsdir = httpdir + '/maps'
pem = serverdir + '/server.pem'
port = int(sys.argv[1]) if len(sys.argv) == 2 else 4343
if not os.path.isfile(pem):
    os.system(f'openssl req -new -x509 -keyout {pem} -out {pem} -days 3650 -nodes -subj /C=US')

_route_get = []
_route_post = []
def route_GET(pattern, fct):
    _route_get.append((re.compile(pattern), fct))
def route_POST(pattern, fct):
    _route_post.append((re.compile(pattern), fct))

games = {}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=httpdir, **kwargs)

    def _redirect301(self, url):
        self.send_response(301)
        self.send_header("Location", url)
        self.end_headers()

    def _send_html(self, html):
        self._send_text(html, "text/html")

    def _send_text(self, text, ctype = "text/plain"):
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.end_headers()
        self.wfile.write(text.encode('utf-8'))

    def dyn_index(self):
        with open(httpdir + '/index.htm', 'r') as f:
            html = f.read()
        subvars = {
                "log_list": "",
                "map_list": "",
                "play_map_list": ""
        }
        for f in sorted(os.listdir(mapsdir)):
            if os.path.isfile(mapsdir + '/' + f):
                if f.endswith('.log'):
                    subvars["log_list"] += f'<p><a href="viewer.htm#maps/{f}">{f}</a></p>\n'
                elif f.endswith('.map'):
                    subvars["map_list"] += f'<p><a href="viewer.htm#maps/{f}">{f}</a></p>\n'
                    subvars["play_map_list"] += f'<p><a href="viewer.htm#playmaps/{f}">{f}</a></p>\n'
        for k, v in subvars.items():
            html = re.sub("{{\s*" + k + "\s*}}", v, html)
        self._send_html(html)

    def dyn_playmaps(self, mapfile):
        gameid = ''.join(random.choices(string.ascii_letters, k=6))
        text = 'PLAYABLE /api/playing/' + mapfile + '/' + gameid + '\n'
        with open(mapsdir + '/' + mapfile, 'r') as f:
            text += f.read()
        self._send_text(text)

    def dyn_playing_api(self, mapfile, gameid):
        with open(mapsdir + '/' + mapfile, 'r') as f:
            m = Map(f.read())
        text = ""
        start = gameid not in games
        if start:
            games[gameid] = (m.startstate, 0)
            text += f"START {m.Sx} {m.Sy} {m.Sz}\n"

        data = self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8')
        mp = Map.pathdesc_pattern.match(data)
        if not mp:
            moves = games[gameid][0] if gameid in games else 0
            text += f'END KO {moves}\n'
            self._send_text(text)
        Ax, Ay, Az = map(int, mp.groups())

        result = m.analyze_path_step(games[gameid][0], Ax, Ay, Az)
        text += f'ACC {Ax} {Ay} {Az}\n'
        if isinstance(result, Map.State):
            games[gameid] = (result, games[gameid][1]+1)
            self._send_text(text)
        else:
            ok, submoves, msg = result
            moves = games[gameid][1] + submoves
            kook = 'OK' if ok else 'KO'
            text += f'END {kook} {moves}\n'
            del games[gameid]
            self._send_text(text)

    def img_bg(self):
        self.path = '/bg.webp'
        super().do_GET()

    def do_GET(self):
        for p, f in _route_get:
            m = p.match(self.path)
            if m:
                g = m.groups() or []
                f(self, *g)
                break
        else:
            super().do_GET()

    def do_POST(self):
        for p, f in _route_post:
            m = p.match(self.path)
            if m:
                g = m.groups() or []
                f(self, *g)
                break
        else:
            super().do_POST()

route_GET(r"^/$", Handler.dyn_index)
route_GET(r"^/static/viewer/bg.webp$", Handler.img_bg)
route_GET(r"^/playmaps/(.+)$", Handler.dyn_playmaps)
route_GET(r"^/index.htm$", lambda s: s._redirect301('/'))
route_POST(r"^/api/playing/([^/]+)/(.+)$", Handler.dyn_playing_api)

with socketserver.TCPServer(("", port), Handler) as httpd:
    print(f'https://{ip()}:{port}/')
    sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    sslctx.load_cert_chain(pem)
    httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    httpd.socket = sslctx.wrap_socket(httpd.socket)
    httpd.serve_forever()

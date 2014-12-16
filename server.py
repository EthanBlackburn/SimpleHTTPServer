import os
import re
import shutil
import socket

class HTTPResponseCode(object):
    def __init__(self, response, message=None, error=False):
        self.response = response
        self.message = message
        self.error = error

    def __repr__(self):
        return self.message


HTTP404 = HTTPResponseCode("404", "<h1>Not Found.</h1>\n", True)
HTTP301 = HTTPResponseCode("301", "Created.\n")
HTTP200 = HTTPResponseCode("200", "Okay.\n")
HTTP500 = HTTPResponseCode("500", "<h1>Bad Gateway.</h1>", True)
HTTP403 = HTTPResponseCode("403", "<h1>Forbidden.</h1>", True)


class SimpleHTTPServer(object):
    def __init__(self, address='127.0.0.1', port=8080):
        self.location = os.path.dirname(os.path.abspath(__file__))
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = address
        self.port = port
        self.conn = None
        self.addr = None

    def run(self):
        self.server.bind((self.host, self.port))
        self.server.listen(10)

        print('Press Ctrl+C to stop server...')

        while True:
            try:
                self.conn, self.addr = self.server.accept()
                msg = self.receive_message()
                request = self.parse_request(msg)
                if request["method"] == 'GET':
                    r = self.GET(request["resource"])
                elif request["method"] == 'POST':
                    r = self.POST(request["resource"])
                elif request["method"] == 'DELETE':
                    r = self.DELETE(request["resource"])
                elif request["method"] == 'PUT':
                    r = self.PUT(request["resource"])
                elif request["method"] == 'OPTIONS':
                    r = self.OPTIONS(request["resource"])
                else:
                    r = HTTP500

                self.conn.send(r.message)
                self.conn.close()

            except KeyboardInterrupt:
                self.server.close()

                return None
                

    def parse_request(self, req):
        request = {}

        line = req.split("\n")
        method, path, protocol = line[0].split(" ")

        request['method'] = method
        request['resource'] = path[1:] if len(path) > 1 else path
        request['protocol'] = protocol

        parse = re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", req)
        request['Content-Type'] = 'text/html;' 
        request['charset'] = 'UTF-8'
        for name, value in parse:
            request[name] = value

        return request

    def receive_message(self, buffsize=4096):
        msg = ''
        while True:
            msg_part = self.conn.recv(buffsize)
            msg += msg_part
            if len(msg_part) < buffsize:
                break

        self.conn.shutdown(socket.SHUT_RD)

        return msg


    def HEAD(self, path):
        if os.path.exists(path):
            return HTTP200
        else:
            return HTTP404

    def DELETE(self, path):
        head = self.HEAD(path)

        if not head.error:
            if(os.path.isdir(path)):
                shutil.rmtree(path)

            else:
                os.remove(path)

            return HTTP200

        return HTTP404


    def GET(self, path):
        head = self.HEAD(path)

        if not head.error:
            if(os.access(path, os.R_OK)): #check if we have privileges
                if(os.path.isdir(path)):
                    self.conn.send(" \n".join(os.listdir(path)))
                    return HTTP200

                else:
                    if(path[-3:] == ".py" and "server.py" not in path): #only run python files for now
                        if(os.access(path, os.X_OK)):
                            os.system("python %s" % path)

                            return HTTP200

                        else:
                            return HTTP500
                    try:
                        data = ""
                        with open(path, 'rb') as f:
                            data += f.read()
                        self.conn.sendall(data)
                    except (TypeError, IOError):
                        return HTTP500

                    return HTTP200
            else:
                return HTTP403

        return HTTP404

    def OPTIONS(self, path):
        head = self.HEAD(path)

        if not head.error:
            self.conn.send("HEAD, POST, PUT, GET, DELETE")

            return HTTP200

        return HTTP404

    def POST(self, path):
        head = self.HEAD(path)

        if not head.error:
            if os.access(path, os.R_OK): #check if we have privileges
                f = os.open(path, os.O_RDWR|os.CREAT)
                f.close()
            else:
                return HTTP403

        return HTTP404

    def PUT(self, path):
        f = os.open(path, os.O_RDWR|os.CREAT)
        f.close()

        return HTTP200


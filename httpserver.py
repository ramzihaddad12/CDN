#!/usr/bin/env python3

from constants import *
import socketserver
import requests
import zlib
import argparse
import http.server
import socket 
# https://docs.python.org/3/library/http.server.html
class HTTPRequestHandler(socketserver.BaseRequestHandler):
    def do_GET(self):
        cm = ''# TODO: the dictionary 
        # Send a 204 status code for beacon
        if self.path == beacon_path:
            self.send_response(204)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            self.wfile.write('BEACON RESPONSE'.encode())

        else:
            path_length =  len(self.path.split('/'))
            # We know that the path length should be at most 2           
            if (path_length <= 2):
                page = self.path.split('/')[-1]

                # Needed content not in cache, so we need to get it from origin
                if page not in cm.CACHE.keys():
                    # Send GET request to the origin server and receive response
                    session = requests.Session()
                    resp = session.get('http://' + origin_server + ':' + str(origin_port) + '/' + page)

                    # status code must be in 200s (successful response), if not send 404 error
                    if resp.status_code < 200 or resp.status_code >= 300:
                       self.send_error(404, '404: NOT FOUND') 

                    else:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Content-length', str(len(resp.content)))
                        self.end_headers()

                        self.wfile.write(resp.content)
                  
                # Needed content in cache, so we need to get it from cache
                else:
                    resp = zlib.decompress(cm.CACHE.get(page))

                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Content-length', str(len(resp)))
                    self.end_headers()

                    self.wfile.write(resp)

                  

            # Send 400 status code
            else:
                self.send_error(400, 'Error')


# Function that gets the source IP address by connecting to another IP address 
# Citation: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
def this_ip_address():

    # Connect to an 8.8.8.8 address to get the source IP address 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))

    return s.getsockname()[0]
if __name__ == '__main__':
    # Parse command and run HTTP server forever
    parser = argparse.ArgumentParser(description='CS5700 CDN Project')
    parser.add_argument("-p", default=SERVER_PORT, action='store_true', type=int, help="Port Number of HTTP Server")
    parser.add_argument("-o", required=True, action='store_true', type = str, help="Name of the origin server for your CDN")
    
    args = parser.parse_args()
    server_port = args.p
    origin_name = args.o 
    # https://docs.python.org/3/library/http.server.html
    with http.server.HTTPServer((this_ip_address(), server_port), HTTPRequestHandler) as server:
        server.serve_forever()
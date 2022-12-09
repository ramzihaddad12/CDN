from constants import *
import urllib.parse

def build_url(uri, host=ORIGIN_SERVER, port=SERVER_PORT):
    return f'http://{host}:{port}/{urllib.parse.quote(uri)}'

def bad_status(status):
    return status >= 300 or status < 200
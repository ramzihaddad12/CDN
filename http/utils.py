from constants import *

def build_url(uri, host=ORIGIN_SERVER, port=SERVER_PORT):
    return f'http://{host}:{port}/{uri}'

def bad_status(status):
    return status >= 300 or status < 200
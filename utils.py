def build_request(host, port, uri) -> str:
    return 'http://' + host + ':' + str(port) + '/' + uri
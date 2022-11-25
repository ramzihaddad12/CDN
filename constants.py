SERVER_PORT = 8080
MAX_CACHE_SIZE = 20000000

PORT_NUMBER = 25006

DNS_SERVER_ADDRESS = "proj4-dns.5700.network"
DNS_SERVER_IP_ADDRESS = "97.107.140.73"

# Map of replicas (we have 2 atm)
REPLICAS = {
    'proj4-repl1.5700.network': '139.144.30.25',
    'proj4-repl2.5700.network': '173.255.210.124'
}

BEACON = "https://cdn-beacon.5700.network/" 
BEACON_PATH = "/grading/beacon"

ORIGIN_SERVER = "cs5700cdnorigin.ccs.neu.edu"
ORIGIN_PORT = 8080

BUILD_SERVER = "cs5700cdnproject.ccs.neu.edu"
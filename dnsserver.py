from constants import * 
from dnslib import * 
import socketserver
import argparse

# Function to choose which replica to send the client to
# ATM, we only have 1 replica, so we have no choice but to send to the 1 available replica
def choose_which_replica(client):
    return replicas[0], replicas_by_IP[0]

# Function that parses incoming DNS packet 
# Citation: https://pypi.org/project/dnslib/
def parse_dns_packet(packet):
    parsed_incoming_packet = DNSRecord.parse(packet)
    
    incoming_query_id = parsed_incoming_packet.header.id
    incoming_query_type = parsed_incoming_packet.q.qtype
    incoming_query_name = parsed_incoming_packet.q.qname
    incoming_query_class = parsed_incoming_packet.q.qclass

    return incoming_query_id, incoming_query_type, incoming_query_name, incoming_query_class

# Function to get the DNS response containg info about replica server that client should redirect to
# Citation: https://pypi.org/project/dnslib/
def get_dns_response_packet(packet, client):
    # Parse DNS Packet
    incoming_query_id, incoming_query_type, incoming_query_name, incoming_query_class = parse_dns_packet(packet)
    # Check if query time is A
    if incoming_query_type != 1:
        raise Exception("Query should be of type A")
    # Choose replica
    chosen_replica, chosen_replica_by_IP = choose_which_replica(client)

    # Creating a DNS Response Packet 
    response_packet = DNSRecord(DNSHeader(id = incoming_query_id, qr=1,aa=1,ra=1), q=DNSQuestion(incoming_query_name, incoming_query_type, incoming_query_class),a=RR(chosen_replica,rdata=A(chosen_replica_by_IP)))
    
    return response_packet.pack()


# https://docs.python.org/3/library/socketserver.html#socketserver.TCPServer
class UDPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Data sent to the socket/ data requested
        data = self.request[0].strip()
        socket = self.request[1]

        dns_record = get_dns_response_packet(data, self.client_address[0])
        socket.sendto(dns_record, self.client_address)


if __name__ == '__main__':
    # Parse command and run DNS server forever
    parser = argparse.ArgumentParser(description='CS5700 CDN Project')
    parser.add_argument("-p", default=port_number, action='store_true', type=int, help="Port Number of DNS Server")
    parser.add_argument("-n", required=True, action='store_true', type = str, help="Name is the CDN-specific name that your server translates to an IP")
    
    args = parser.parse_args()
    server_port = args.p
    server_name = args.n # name is the CDN-specific name that your server translates to an IP.
    
    with socketserver.UDPServer((dns_server_ip_address, server_port), UDPRequestHandler) as server:
        server.serve_forever()
# https://github.com/maxmind/GeoIP2-python
import maxminddb
import math
import sys
import argparse
from constants import *


class ReplicaSelector:
    def __init__(self):
        # this is an expensive operation - do as limited as possible
        self.reader = maxminddb.Reader('geoipdata.mmdb')

    def __del__(self):
        # close reader when class is destroyed
        self.reader.close()

    # return (lat, lon) of the given ip_addr
    def get_location(self, ip_addr):
        response = self.reader.get(ip_addr)
        return response['location']['latitude'], response['location']['longitude']

    # https://www.movable-type.co.uk/scripts/latlong.html
    # get distance bewteen two locations (in km) using Haversine formula
    def get_distance_between(self, loc1, loc2):
        # radius of earth in km
        R = 6371

        lat1 = math.radians(loc1[0])
        lat2 = math.radians(loc2[0])
        d_lat = lat2 - lat1

        lon1 = math.radians(loc1[1])
        lon2 = math.radians(loc2[1])
        d_lon = lon2 - lon1

        # square of half the chord length between points
        a = (math.sin(d_lat / 2) ** 2) + \
            (math.cos(lat1) * math.cos(lat2)) * \
            (math.sin(d_lon/2) ** 2)

        # angular distance in radians
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c


    # return the closest replica for the client_ip
    def get_closest_replica(self, client_ip):
        # lat, lon of the client
        client_loc = self.get_location(client_ip)
        
        # placeholder values - assume replica1 is best
        repl1 = 'proj4-repl1.5700.network'
        best_replica = (repl1, REPLICAS[repl1])
        min_dist = sys.float_info.max

        # iterate through replicas to find closest one to client
        for repl_name, repl_ip in REPLICAS.items():
            repl_loc = self.get_location(repl_ip)
            dist = self.get_distance_between(client_loc, repl_loc)

            if dist < min_dist:
                min_dist = dist
                best_replica = (repl_name, repl_ip)

        return best_replica



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replica Selector')
    parser.add_argument("-ip", required=True, action='store', type=str, help="Client IP Address")

    args = parser.parse_args()
    ip = args.ip

    replicaSelector = ReplicaSelector()
    closest_replica = replicaSelector.get_closest_replica(ip)
    dist = replicaSelector.get_distance_between(replicaSelector.get_location(ip), replicaSelector.get_location(closest_replica[1]))
    print(f'Closest replica is {closest_replica} with distance {dist} km')

import csv
import os
import zlib
import requests
import utils
import argparse


# CONSTANTS
SERVER_PORT = 8080
CACHE_SIZE = 20000000
CACHE_PATH = os.getcwd() + '/cache'


class Cacher:
	def __init__(self, hostname):
		self.hostname = hostname
		self.unused_cache = CACHE_SIZE

	# parse pageviews and populate the cache
	def populate(self): 
		# make directory if not already exists
		if not os.path.exists(CACHE_PATH):
			os.mkdir(CACHE_PATH)

		# parse pageviews
		with open('pageviews.csv', 'r') as file, requests.Session() as session:
			page_popularities = csv.reader(file)
			for page in page_popularities:
				# send request for page
				rank = page[0]
				resp = session.get(
						utils.build_request(self.hostname, SERVER_PORT, rank))

				# try to add to cache, stop parsing csv if cache full
				cache_available = self.try_add_to_cache(resp, rank)
				if not cache_available:
					break


	# try to add resp to cache
	# return False if cache is full, True otherwise
	def try_add_to_cache(self, resp, rank):
		# status code must be in 200s (successful response)
		if resp.status_code < 200 or resp.status_code >= 300:
			return True

		# if adding resp to cache would overflow, return False
		resp_compressed = zlib.compress(resp)
		if self.unused_cache - len(resp_compressed) < 0:
			return False

		# add to cache, update unused cache size
		filename = os.path.join(CACHE_PATH, rank)
		with open(filename, 'wb') as cached_file:
			cached_file.write(resp_compressed)

		self.unused_cache -= len(resp_compressed)
		return True


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('-o', 
        dest='hostname', 
        type=str, action='store', 
        required=True)
    args = arg_parser.parse_args()

    hostname = args.hostname
    cacher = Cacher(hostname)
    cacher.populate()


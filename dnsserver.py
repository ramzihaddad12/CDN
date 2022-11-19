from constants import * 
from dnslib import * 

class DNS():
    def __init__(self):

    # Function to choose which replica to send the client to
    # ATM, we only have 1 replica, so we have no choice but to send to the 1 available replica
    def choose_which_replica(self):
        return replicas[0]

    def dig(self):


        # Check if query time is A
        if == 1:
            return 

        else:
            




if __name__ == '__main__':
    # Parse command and run DNS 
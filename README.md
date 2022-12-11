# cs5700-project5-python3

## High Level Approach
Our high level approach revolved around using a caching strategy that prioritizes more popular content and using a geoip database to select the "best" replica to send a client to. We relied on several Python libraries that helped in simplifying the task, such as dnslib and socketserver. 

## DNS & HTTP Implementions
#### DNS Implementation
The dnsserver program heavily utilizes the TCPServer class in socketserver library (https://docs.python.org/3/library/socketserver.html#socketserver.TCPServer). Using a UDP Request Handler, the incoming DNS requests are handled. This involves parsing the incoming DNS packets to find out what the query id, name, type, and class are using dnslib. Since this implementation only requires us to respond to DNS queries that are of A-type, we check if the incoming record has that type before responding. In terms of the response, a DNS packet is built (also using dnslib) containing the IP address information of the replica chosen to handle the content request. For this project, the decision of choosing a replica server is based on a geoip database. 
 
 TODO: talk more about geoip here
 
#### HTTP Implementation
The httpserver program heavily utilizes the HTTPServer class in socketserver library (https://docs.python.org/3/library/http.server.html). Using a HTTP Request Handler, the incoming content requests are handled. The httpserver program is run on each of the replicas seperately. There are two main cases to handle for incoming requests. The first case is when the content that is requested is already present in the replica's cache, and in that case, the replica would just get the content from its cache and respond back with it to the client using HTTP. The second case is when the content is not in the cache, which requires the replica to fetch that content from the origin server, which contains all the content available, and then serving back to the client, thus basically acting as a "middle man".

TODO: talk about caching: how we cached and compression

## Challenges Faced
- Learning about bash scripting: syntax and passing arguments through those scripts
- Learning about parsing DNS packets (using dnslib) and testing using dig
- Working with ssh keys
- Learning about chmod and its use cases
- 

## Work Distribution
The work distribution mainly was divided between different layers of setting up the CDN and the detailed functionalities needed. Ramzi worked on writing the bash scrips for running the CDN, deploying the CDN, and stopping it. In addition, Ramzi was responsible for setting up the DNS server and replicas in terms of making sure they are running correctly, and that both these types of servers can handle requests. This involved working on receiving DNS packets to find out the client IP address and query type and responding with or building DNS packets to redirect the client to the closest server. 

## Future Steps
Had time permitted, we would have worked on trying to incorporate active measurement to better performance instead of just relying on a geographical database.

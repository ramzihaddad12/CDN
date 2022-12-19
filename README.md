# Content Delivery Network

## High Level Approach
Our high level approach revolved around using a caching strategy that prioritizes more popular content and using a geoip database to select the "best" replica to send a client to. We relied on several Python libraries that helped in simplifying the task, such as dnslib, socketserver, and maxminddb. 

## DNS & HTTP Implementions
### DNS Implementation
The dnsserver program heavily utilizes the TCPServer class in [socketserver library](https://docs.python.org/3/library/socketserver.html#socketserver.TCPServer). Using a UDP Request Handler, the incoming DNS requests are handled. This involves parsing the incoming DNS packets to find out what the query id, name, type, and class are using dnslib. Since this implementation only requires us to respond to DNS queries that are of A-type, we check if the incoming record has that type before responding. In terms of the response, a DNS packet is built (also using dnslib) containing the IP address information of the replica chosen to handle the content request. For this project, the decision of choosing a replica server is based on a geoip database. 
 
We implemented replica selection by proximity using a geo IP database. We used maxminddb to parse the geo IP database to get a client's latitude and longitude, and then iterated through our replica servers to find the closest one by calculating its distance to the client using the [Haversine formula](https://www.movable-type.co.uk/scripts/latlong.html). If we didn't have geo data for an IP address, we defaulted to using replica 1.
 
### HTTP Implementation
The httpserver program heavily utilizes the HTTPServer class in [socketserver library](https://docs.python.org/3/library/http.server.html). Using a HTTP Request Handler, the incoming content requests are handled. The httpserver program is run on each of the replicas seperately. There are two main cases to handle for incoming requests. The first case is when the content that is requested is already present in the replica's cache, and in that case, the replica would just get the content from its cache and respond back with it to the client using HTTP. The second case is when the content is not in the cache, which requires the replica to fetch that content from the origin server, which contains all the content available, and then serving back to the client, thus basically acting as a "middle man".

To build the cache, each replica holds onto how much disk space it uses by first calculating the size of the source code in the directory. It then requests pages sequentially by popularity following the zipf distribution, and compresses the content of each page. The compressed content gets written to `/cache`, where it can be read during the run phase. We run this locally in the `/http` folder to generate the cache, simulating what would happen on a replica. This cache folder is recursively copied over to the base directory.

## Challenges Faced
- Learning about bash scripting: syntax and passing arguments through those scripts
- Learning about parsing DNS packets (using dnslib) and testing using dig
- Working with ssh keys
- Learning about chmod and its use cases
- Configuring libraries for parsing .mmdb files when deploying
- Optimizing caching strategy to not exceed 20 MB

## Work Distribution
The work distribution mainly was divided between different layers of setting up the CDN and the detailed functionalities needed. Ramzi worked on writing the bash scrips for running the CDN, deploying the CDN, and stopping it. In addition, Ramzi was responsible for setting up the DNS server and replicas in terms of making sure they are running correctly, and that both these types of servers can handle requests. This involved working on receiving DNS packets to find out the client IP address and query type and responding with or building DNS packets to redirect the client to the closest server. John worked on generating the caching strategy to make sure we didn't exceed 20 MB on disk during the deploy phase. John also worked on the httpserver code to pull the files written in the deploy phase to memory. John also worked on parsing .mmdb files to select the closest replica to a client address to help the DNS server respond for the closest replica IP to type A queries.

## Future Steps
Had time permitted, we would have worked on trying to incorporate active measurement to better performance instead of just relying on a geographical database. When a client connected for the first time, we would have fallen back to use our geo IP implementation as a "best guess" solution. When the DNS server could pull RTT information from the replicas to client, we would choose the lowest RTT from the replica to client when responding to the type A queries.

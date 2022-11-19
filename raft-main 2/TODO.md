
# List of things that we should still do

1. Investigate using `select.select` instead of raising a timeout in the socket library
    * I believe that this is causing some latency which is resulting in higher latency between client/server

1. Implement logic for when a Candidate times out
    * I believe that this should be an election restart with the candidates determined election timeout
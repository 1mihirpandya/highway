# A distributed peer-to-peer fileshare system
Highway is a distributed P2P network that allows users to connect, search for files, and download files. Think Gnutella in terms of similar software/tools.

## Basic architecture/design:
<img width="800" alt="Screen Shot 2020-06-28 at 1 35 39 AM" src="https://user-images.githubusercontent.com/7907525/85943316-1efa5d00-b8e4-11ea-8433-eee418d57cbf.png">
Basic structure of a client and Gatekeeper.

<img width="500" alt="Screen Shot 2020-06-28 at 2 00 47 AM" src="https://user-images.githubusercontent.com/7907525/85943297-05591580-b8e4-11ea-8231-e09eca5ec1b8.png">
What the network would look like in a minimal failure scenario (1 is the first client to join the network). The clustering/shape of the graph minimizes the number of hops to reach the maximum number of peers when making queries that require forwarding.

### Gatekeeper:
Gatekeeper is a service that essentially acts as a client registry and gateway to the network. Clients query Gatekeeper for potential neighbors when they want to join the network, and also send periodic updates about their status/neighbor count. As every client communicates with Gatekeeper on a regular interval, availability, concurrency, and speed are very important.

- Gatekeeper uses Flask
- Uses Redis as a DB
- Both Gatekeeper and Redis are deployed via Kubernetes
- Gatekeeper is replicated to maintain availability and concurrency
- Redis uses two pods (a master and a replica) to serve Gatekeeper requests quickly and concurrently

All the Gatekeeper code, Dockerfiles, and Kubernetes deployment files can be found in the Docker_Kubernetes folder. There are two versions of Redis, one which uses images from the Google/Docker repository, and one which was custom made.

### The client:
The client is comprised of a few distinct components: the shell interface, the app layer/Gatekeeper client, the file service, the client/query service, the network client, and the file & network cache. The structure of these layers can be seen in the diagram above. In this system, clients are the key drivers, and act as servers themselves; they maintain states of internal configurations (like files, file paths, neighbors, etc.), and also cache the state of their neighbors. Neighbors maintain their connections by heartbeating. Queries and other requests are all sent/pass through clients. As some types of queries (like getting files and connecting to neighbors) are more important and can’t afford packet drops, they are serviced using TCP messages, while majority of other queries are serviced using UDP messages. Below is a list of what features each component handles:

#### The application layer:
Mainly acts as a hook and delegator for all methods/functionalities.
- Implements the connection protocol
    - Will check if a potential neighbor is “valid” upon receiving said potential neighbor from Gatekeeper
    - If not, the protocol will use BFS and traverse through all of the potential neighbor’s neighbors until it finds another candidate
    - If no candidate is found, the client will query Gatekeeper for a potential neighbor again and continue searching 

#### The client/query service:
This service handles the core implementation, query building process, and sending/forwarding delegation of all requests.
- Implements a pseudo-RPC protocol for easy interfacing from the application layer
- Implements query forwarding and delegation of query caching
- Implements non-blocking query waiting when forwarding requests
    - Sends a valid query back when it gets one, or waits on all responses and sends one back
    - Also implements a query timeout in the case of dropped response packets
- Implements network cache cleanup and updates
    - Updates neighbor cache state whenever it receives a heartbeat
    - Does lazy cleanup for stale or completed cached queries
- Implements heartbeating
    - Periodically sends all neighbors UDP heartbeats
    - Piggybacks file lists and neighbor lists on the heartbeats
- Implements failure detection
    - Maintains neighbor status (OKAY, WARNING, and FAILED)
    - If a heartbeat hasn’t been received within a specific period of time, the client sets the neighbor’s status to WARNING
    - When a neighbors status is WARNING, the client will uses a non-blocking FD system similar to SWIM 
    - If no response is received from SWIM, the neighbor will be marked as failed and deleted
    - The client will also notify Gatekeeper of the failed client, then attempt to connect to one of the failed client’s neighbors to maintain the network overlay graph
- Implements false positive failure detection
    - If a client receives heartbeats from a non-neighbor, the client will notify the non-neighbor to remove it from its neighbor list

#### The file service:
This service handles the core implementation and query building process related to getting files/streaming.
- Implements sync UDP query
- Implements query response streaming interface
    - Uses network client building blocks to implement TCP streaming
    - Main use: streaming large files quickly and efficiently
- Implements file dependency updates
    - Traverses file list and root folder for changes
    - Updates file list and file cache based on said changes

#### The network client:
This service contains the core building blocks/implementation of network communication, including sending UDP/TCP requests The network client always has two threads running, one to handle TCP requests, and one to handle UDP requests.
- Implements basic TCP and UDP message sending
- Listens to a TCP port and UDP port with two threads to service requests and heartbeats
- Caches request/neighbor metadata when requests are received

#### The network cache and file cache:
- Stores state of client’s neighbors (file lists, neighbors of neighbor, last message sent, last ACK received)
- Stores all forwarded queries and query info (forwarded query tracing, timestamps, 
- Caches query hits with temporary persistence, keeps more popular requests for longer
- Stores all file folder structure/dependencies
- Thread safe and null value/collision safe

Majority of the client architecture was built to be delegate-oriented, so specific changes in one file/service wouldn’t cascade and require changes in other files/services. The client architecture was also built to be non-blocking and fault tolerant. All the underlying services, like UDP/TCP listening, heartbeating, failure detection, file dependency updates, and Gatekeeper updates are all on individual threads. Handling queries and responses are also mainly done on new threads to allow the client to continue listening for new messages. Parts of the client architecture (namely the caches) are protected to be thread safe and error safe. The functions that may require protection are wrapped with decorators.


## Starting Highway:

The first thing that needs to be started is Gatekeeper:

	kubectl apply -f Docker_Kubernetes/redis/redis-master-service.yaml
	kubectl apply -f Docker_Kubernetes/redis/redis-follower-service.yaml
	kubectl apply -f Docker_Kubernetes/gatekeeper/gatekeeper-service.yaml

	kubectl apply -f Docker_Kubernetes/redis/redis-master-deployment.yaml
	kubectl apply -f Docker_Kubernetes/redis/redis-follower-deployment.yaml
	kubectl apply -f Docker_Kubernetes/gatekeeper/gatekeeper-deployment.yaml

Remember to apply the services first, as Gatekeeper looks for env variables set by the reds services. The Redis-related commands above use the Google/Docker images for Redis. My Dockerfile/deployments/services can be found in the redis-custom folder.

If using minikube, the load balancer service used for Gatekeeper will not give a public external IP address. In this case, perform the following command to get the external IP: `minikube service gatekeeper --url`

The IP should be put in the `GatekeeperClient.py` file. To start the Highway client, simply run `python Shell.py` in the main directory. The system requires python3. To connect to the network, enter `start <root_folder>`, where the <root_folder> has the files that you’re willing to have shared/downloaded. Other commands can be found in Shell.py.

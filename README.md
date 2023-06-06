# Python Load Balancer

Python load balancer built with asyncio and aiohttp. A simple Flask backend server is provided for example.

Servers are sent health checks over HTTP periodically. Servers that don't respond will be removed from the pool.

# Usage

The load balancer is launched from the shell. The script takes two command line arguments: 

1. The period at which health checks are sent (in seconds), and
2. The number of backend servers.

> python lb.py 10 2

The network details of the load balancer and backend servers should be written into the .env as in the example provided. The .env should have:

* Load Balancer listening port
* The URL of the backend status checking endpoint
* Hostname and port for each server

# Dependencies

> pip install aiohttp

> pip install Flask

> pip install python-dotenv
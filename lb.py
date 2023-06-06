import aiohttp
import asyncio
from dotenv import load_dotenv
import os
import sys

index = 0

argc = len(sys.argv)
argv = sys.argv

load_dotenv()

if argc != 3:
    print("Usage: python lb.py $HEALTHPERIOD $NUMSERVERS")
    sys.exit(1)

LBPORT = int(os.getenv("LISTENPORT"))
HOST = 'localhost'
PERIOD = int(argv[1])

numServers = int(argv[2])
BACKENDSERVERS = []
for i in range(1, numServers+1):
    serverHost = os.getenv(f"BACKENDHOST{i}")
    serverPort = os.getenv(f"BACKENDPORT{i}")

    if serverHost is None or serverPort is None:
        print(f'Error: Could not read server {i} info from .env')
        sys.exit(1)
    serverPort = int(serverPort)
    BACKENDSERVERS.append((serverHost, serverPort))
DOWNSERVERS = {}


def round_robin(length):
    global index
    global DOWNSERVERS
    choice = index
    choice = (choice + 1) % length
    while choice in DOWNSERVERS:
        choice = (choice + 1) % length
    index = choice
    return choice

def choose_server():
    global numServers
    if len(DOWNSERVERS.keys()) == numServers:
        return -1
    choice = round_robin(numServers)
    return choice

async def balance_load(reader, writer):
    # Read request from client
    data = await reader.read(512)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    
    print(f"Received {message}from {addr}")

    # Forward request to backend server
    choice = choose_server()
    if choice < 0:
        print('No backend servers are available')
        writer.close()
        return
    
    backend, port = BACKENDSERVERS[choice]
    print(backend, port)

    try:
        r, w = await asyncio.open_connection(backend, port)
    except ConnectionRefusedError:
        print('Connection refused by backend')
        writer.close()
        global DOWNSERVERS
        DOWNSERVERS[choice] = True
        return
    w.write(data)
    await w.drain()

    # Read response from backend
    backend_message = await r.read(512)
    print(f"Received from server:{backend_message.decode()}")
    w.close()

    # Forward response to client
    writer.write(backend_message)
    await writer.drain()

    writer.close()
    await writer.wait_closed()
    

async def serve():
    # Start a server on (HOST, PORT), pass in the list of backend servers
    server = await asyncio.start_server(balance_load, HOST, LBPORT)
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

async def main():
    #run the server and one health check function for each server concurrently
    await asyncio.gather(serve(), *(health_check(i) for i in range(len(BACKENDSERVERS))))
    
async def health_check(index):
    timeout = aiohttp.ClientTimeout(total=5)
    status_url = os.getenv('STATUS_URL')
    global DOWNSERVERS
    while True:
        print(f'Health check on server {index+1}')
        host, port = BACKENDSERVERS[index]
        # open a tcp session w backend server and do http get to /status
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"http://{host}:{port}/{status_url}", timeout=timeout) as resp:
                    print(resp.status)
                    print(await resp.text())
                    if index in DOWNSERVERS:
                        del DOWNSERVERS[index]
            except asyncio.exceptions.TimeoutError:
                print(f"Health check timed out on server {index+1}")
                DOWNSERVERS[index] = True
            except aiohttp.ClientConnectionError:
                print(f"Could not connect to backend {index+1}")
                DOWNSERVERS[index] = True

        await asyncio.sleep(PERIOD)

if __name__ == "__main__":
    routines = []
    asyncio.run(main())
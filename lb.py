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
BACKENDSERVERS = [(os.getenv(f"BACKENDHOST{i}"), int(os.getenv(f"BACKENDPORT{i}"))) for i in range(1, numServers+1)]
DOWNSERVERS = {}


def round_robin(length):
    global index
    global DOWNSERVERS
    choice = index
    index = (index + 1) % length
    while index in DOWNSERVERS:
        index = (index + 1) % length
    return choice

def choose_server():
    global BACKENDSERVERS
    choice = round_robin(len(BACKENDSERVERS))
    return BACKENDSERVERS[choice]

async def balance_load(reader, writer):
    # Read request from client
    data = await reader.read(512)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    
    print(f"Received {message}from {addr}")

    # Forward request to backend server
    backend, port = choose_server()
    print(backend, port)

    #open async connection to backend server
    # TODO fix bug where this funct gets health check response
    # TODO add check if server is in down servers map
    # TODO add try except block to check if connection fails...
    r, w = await asyncio.open_connection(backend, port)
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
    while True:
        print(f'Health check on server {index}')
        host, port = BACKENDSERVERS[index]
        # open a tcp session w backend server and do http get to /status
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{host}/{status_url}:{port}", timeout=timeout) as resp:
                print(resp.status)
                print(await resp.text())
        await asyncio.sleep(PERIOD)

if __name__ == "__main__":
    routines = []
    asyncio.run(main())
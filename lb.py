import asyncio
from dotenv import load_dotenv
import os
import sys

index = 0

def round_robin(length):
    global index
    choice = index
    index = (index + 1) % length
    return choice

def choose_server(servers):
    choice = round_robin(len(servers))
    return servers[choice]

async def balance_load(reader, writer, servers):
    # Read request from client
    data = await reader.read(512)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    
    print(f"Received {message}from {addr}")

    # Forward request to backend server
    backend, port = choose_server(servers)
    print(backend, port)

    #open async connection to backend server
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
    

async def main():
    argc = len(sys.argv)
    argv = sys.argv

    load_dotenv()

    if argc != 3:
        print("Usage: python lb.py $HEALTHPERIOD $NUMSERVERS")
        return 1
    
    LBPORT = int(os.getenv("LISTENPORT"))
    HOST = 'localhost'

    numServers = int(argv[2])
    BACKENDSERVERS = [(os.getenv(f"BACKENDHOST{i}"), int(os.getenv(f"BACKENDPORT{i}"))) for i in range(1, numServers+1)]
        
    # Start a server on (HOST, PORT), pass in the list of backend servers
    server = await asyncio.start_server(lambda r, w: balance_load(r, w, BACKENDSERVERS), HOST, LBPORT)
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
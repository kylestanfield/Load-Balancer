import asyncio
import sys

async def balance_load(reader, writer, backend):
    # Read request from client
    data = await reader.read(512)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    
    print(f"Received {message}from {addr}")

    #DEBUG
    print(f"Send {message} to {backend} on port {81}")

    # Forward request to backend server
    r, w = await asyncio.open_connection(backend, 81)
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

    if argc < 3:
        print("Usage: python lb.py $PORT $BACKENDHOST")
        return 1
    
    PORT = int(argv[1])
    #BACKENDHOST = argv[2]
    #DEBUG
    BACKENDHOST = '127.0.0.1'
    #HOST = socket.gethostname()
    #DEBUG
    HOST = '127.0.0.1'

    server = await asyncio.start_server(lambda r, w: balance_load(r, w, BACKENDHOST), HOST, PORT)
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
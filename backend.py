import socket
import sys

def main():
    argc = len(sys.argv)
    argv = sys.argv

    if argc < 3:
        print("Usage: python lb.py $PORT $HOST")
        return 1
    
    PORT = int(argv[1])
    HOST = argv[2]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.bind((HOST, PORT))
    except socket.error as msg:
        print(f'Bind to socket failed. Error code: {str(msg[0])} Message: {str(msg[1])}')
        return 1


    while True:
        sock.listen(5)
        conn, addr = sock.accept()
        print(f'Received request from {addr[0]}: {str(addr[1])}')
        data = conn.recv(2048)
        print(data.decode())

        conn.send(b'HTTP/1.1 200 OK\nContent-Type: text/html\n\nHello from the backend!')

if __name__ == '__main__':
    main()
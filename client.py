import socket
import select
import sys


def getServerAddrs(filename):
    addrServers = []
    fd = open(filename, 'r')
    for line in fd:
        addrServers.append((line.split(':')[0], int(line.split(':')[1])))
    fd.close()
    return addrServers

def try_connect_to_server(sock, addrServers):
    for addr in addrServers:
        flg = sock.connect_ex(addr)
        if flg == 0:
            return 0
    return 1



def chat_client():
    addrServers = []
    sizeBuf = 4096

    print('Input name:')
    name = sys.stdin.readline()[:-1] + ': '
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    addrServers = getServerAddrs('server_list')
    if try_connect_to_server(sock, addrServers):
        print('Not available server')
        return 1
    epoll = select.epoll()
    epoll.register(sock.fileno(), select.EPOLLIN)
    epoll.register(sys.stdin.fileno(), select.EPOLLIN)

    while 1:
        pairs = epoll.poll()
        for fileno, event in pairs:
            if event & select.EPOLLIN:
                if fileno == sock.fileno():
                    msg = sock.recv(sizeBuf)
                    if msg:
                        msg = msg.decode()
                        print(msg)
                    else:
                        print(sock.getsockname())
                        if try_connect_to_server(sock, addrServers):
                            print('Not available server')
                            return 1
                elif fileno == sys.stdin.fileno():
                    msg = name + sys.stdin.readline()
                    sock.send(msg.encode())
                    print(msg)

if __name__ == "__main__":
    chat_client()
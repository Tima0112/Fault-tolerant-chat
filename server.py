import sys
import socket
import select
import pdb




def try_bind(addrServers):
    sock = socket.socket()
    flg = 1
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    fd = open('server_list', 'r')
    for line in fd:
        ipPort = (line.split(':')[0], int(line.split(':')[1]))
        if flg:
            try:
                sock.bind(ipPort)
                sock.listen(10)
                flg = 0
            except socket.error:
                addrServers.append(ipPort)
                continue
        else:
            addrServers.append(ipPort)
    fd.close()
    if flg == 1:
        return None
    else:
        return sock


def chat_server():
    socketsClient = {}
    socketsServer = {}
    addrServers = []
    sizeBuf = 1024
    # pdb.set_trace()
    serversock = try_bind(addrServers)
    if serversock == None:
        print('All addresses is busy')
        return
    serversock.co
    epoll = select.epoll()
    epoll.register(serversock.fileno(), select.EPOLLIN)
    while 1:
        pairs = epoll.poll(maxevents=1)
        fileno, event = pairs[0]
        if fileno == serversock.fileno():
            conn, addr = serversock.accept()
            epoll.register(conn.fileno(), select.EPOLLIN)
            try:
                addrServers.index(addr)
            except:
                pass




if __name__ == '__main__':
    chat_server()


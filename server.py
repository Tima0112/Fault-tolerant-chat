import sys
import socket
import select
import pdb



def try_bind(addrServers):
    sock = socket.socket()
    flg = 1
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    fd = open('server_list', 'r')
    i = 0
    for line in fd:
        ipPort = (line.split(':')[0], int(line.split(':')[1]))
        if flg:
            try:
                sock.bind(ipPort)
                sock.listen(10)
                flg = 0
                index = i
            except socket.error:
                addrServers.append(ipPort)
        else:
            addrServers.append(ipPort)
        i += 1

    fd.close()
    if flg == 1:
        return None, index
    else:
        return sock, index


def try_connect_server(addrServers, myindex):
    sock = socket.socket()
    sock.bind((addrServers[myindex][0], addrServers[myindex][1] + 1))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    for addr in addrServers:
        flg = sock.connect_ex(addr)
        if flg == 0:
            return sock
    return None


def send_hist(sock, fd):
    fd.seek(0, 0)
    buf = fd.read()
    sock.send(buf)


def broadcast(socketsClient, msg):
    for sock in socketsClient:
        try:
            sock.send(msg)
        except:
            sock.close()
            if sock in socketsClient:
                socketsClient.pop(sock.fileno())


def chat_server():
    socketsClient = {}
    addrServers = []
    sizeBuf = 1024
    # pdb.set_trace()
    serversock, myindex = try_bind(addrServers)
    if serversock == None:
        print('All addresses is busy')
        return
    fdw = open('hist' + str(myindex), 'a')
    fdr = open('hist' + str(myindex), 'r')
    epoll = select.epoll()
    epoll.register(serversock.fileno(), select.EPOLLIN)
    otherServer = try_connect_server(addrServers, myindex)
    if otherServer != None:
        epoll.register(otherServer.fileno(), select.EPOLLIN)

    while 1:
        pairs = epoll.poll()
        for fileno, event in pairs:
            if fileno == serversock.fileno():
                sock, addr = serversock.accept()
                sock.setblocking(0)
                socketsClient[sock.fileno()] = sock
                epoll.register(sock.fileno(), select.EPOLLIN)
                addr = (addr[0], addr[1] - 1)

                if otherServer != None and (addr not in addrServers):
                    epoll.unregister(otherServer.fileno())
                    otherServer = None
                send_hist(sock, fdr)
            elif event & select.EPOLLIN:
                sock = socketsClient[fileno]
                try:
                    data = sock.recv(sizeBuf)
                    if data:
                        broadcast(socketsClient, data)
                        fdw.write(data)
                        fdw.flush()
                    else:
                        if sock in socketsClient:
                            socketsClient.pop(sock.fileno())
                            print("Client (%s, %s) is offline" % addr)
                except:
                    if sock in socketsClient:
                        socketsClient.pop(sock.fileno())
                        print("Client (%s, %s) is offline" % addr)


if __name__ == '__main__':
    chat_server()


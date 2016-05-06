#!/usr/bin/env python3

import socket
import select
import sys
import os
from datetime import datetime, date, time

def getServerAddrs(filename):
    addrServers = []
    fd = open(filename, 'r')
    for line in fd:
        addrServers.append((line.split(':')[0], int(line.split(':')[1])))
    fd.close()
    return addrServers

def try_connect_to_server(addrServers, epoll):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    for addr in addrServers:
        flg = sock.connect_ex(addr)
        if flg == 0:
            epoll.register(sock.fileno(), select.EPOLLIN)
            return sock
    return None

def clear():
    for i in range(10):
        print('\n')

def disconnect(sock, addrServers, epoll):
    try:
        epoll.unregister(sock.fileno())
        sock.close()
    except:
        pass
    clear()
    sock = try_connect_to_server(addrServers, epoll)
    if sock == None:
        print('Not available server')
        sys.exit(1)
    else: return sock

def chat_client():
    addrServers = []
    sizeBuf = 4096
    print("Welcome to super chat room!\nTo leave input exit ;)")

    print('Input name:')
    name = sys.stdin.readline()[:-1] + ': '

    addrServers = getServerAddrs('server_list')
    epoll = select.epoll()
    epoll.register(sys.stdin.fileno(), select.EPOLLIN)
    sock = try_connect_to_server(addrServers, epoll)

    if sock == None:
        print('Not available server')
        return 1

    while 1:
        pairs = epoll.poll()
        for fileno, event in pairs:
            if event & select.EPOLLIN:
                if fileno == sock.fileno():
                    msg = sock.recv(sizeBuf)
                    if msg:
                        msg = msg.decode()
                        print(msg[:-1])
                    else:
                        sock = disconnect(sock, addrServers, epoll)
                elif fileno == sys.stdin.fileno():
                    buf = sys.stdin.readline()
                    time = datetime.now().strftime("(%H:%M:%S) ")
                    if buf == "exit\n":
                        msg = time + name + "Bye all!\n"
                        sock.send(msg.encode())
                        sock.close()
                        print("Exit from chat")
                        return 1
                    msg = time + name + buf
                    sock.send(msg.encode())
                    print(msg[:-1])

if __name__ == "__main__":
    chat_client()
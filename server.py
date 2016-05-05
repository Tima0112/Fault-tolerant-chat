import sys
import socket
import select
import pdb
import pickle
import copy

class Message:
    types = ['msg', 'tree']
    type = ''

    def __init__(self, type, msg=None, tree=None):
        index = self.types.index(type)
        self.type = self.types[index]
        if index == 0:
            self.msg = copy.copy(msg)
        elif index == 1:
            self.tree = copy.deepcopy(tree)




class Chat_server:
    addrServers = []
    socketsClient = {}
    socketsServer = {}
    parentSock = None
    parentIndex = -1
    sock = None
    tree_conn = {}
    sizeBuf = 4096
    fdr = None
    fdw = None
    epoll = None

    def try_bind(self, filename):
        sock = socket.socket()
        flg = 1
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        fd = open(filename, 'r')
        i = 0
        for line in fd:
            ipPort = (line.split(':')[0], int(line.split(':')[1]))
            if flg:
                try:
                    sock.bind(ipPort)
                    sock.listen(10)
                    flg = 0
                    self.index = i
                    print('bind (%s, %d)' % ipPort)
                except socket.error:
                    pass
            self.addrServers.append(ipPort)
            i += 1

        fd.close()
        if not flg:
            self.sock = sock
            self.tree_conn[self.index] = []
        else:
            sock.close()
            raise Exception('All addresses is busy')

    def try_connect_parent(self, epoll):
        addrServers = self.addrServers
        if self.parentSock != None:
            self.parentSock.close()

        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((addrServers[self.index][0], addrServers[self.index][1] + 1))

        if self.parentSock == None:
            size = len(addrServers)
            curindex = self.index
            for i in range(size - 1):
                curindex = [curindex - 1, size - 1][curindex - 1 < 0]
                flg = sock.connect_ex(addrServers[curindex])
                if flg == 0:
                    self.parentSock = sock
                    self.parentIndex = curindex
                    self.socketsServer[self.parentSock.fileno()] = (sock, curindex)
                    epoll.register(self.parentSock.fileno(), select.EPOLLIN)
                    print("Parent Server is: №{} {}\n"\
                          .format(self.parentIndex, self.addrServers[self.parentIndex]))
                    return 0
            return 1
        else:
            self.parentSock = sock
            parent = self.parentIndex
            rval = self.tree_conn[parent].index(self.index)
            list_servers = self.tree_conn[parent].copy()[:rval] + [self.parentIndex,]
            while 1:
                for index in list_servers:
                    if self.index == index:
                        continue
                    flg = self.parentSock.connect_ex(addrServers[index])
                    if flg == 0:
                        subtree = self.tree_conn[self.index].copy()
                        self.tree_conn.clear()
                        self.tree_conn[self.index] = subtree
                        self.parentIndex = index
                        self.socketsServer[self.parentSock.fileno()] = (self.parentSock, index)
                        epoll.register(self.parentSock.fileno(), select.EPOLLIN)
                        print("Parent Server is: №{} {}\n" \
                              .format(self.parentIndex, self.addrServers[self.parentIndex]))
                        return 0
                    else:
                        try:
                            self.tree_conn[parent].remove(index)
                        except:
                            if index == parent:
                                self.tree_conn.pop(parent)
                flg = 0
                for key, childs in self.tree_conn.items():
                    if parent in childs:
                        parent = key
                        rval = len(childs)
                        list_servers = self.tree_conn[parent].copy() + [parent,]
                        #self.childs.remove(parent)
                        flg = 1
                        break

                if flg == 0:
                    return 1




    def send_allhist(self, sock, fd):
        fd.seek(0, 0)
        buf = fd.read()
        try:
            if sock.fileno() in self.socketsServer.keys():
                msg = Message('msg', msg=buf)
                msg = pickle.dumps(msg)
                sock.send(msg)
                flg = 1
            elif sock.fileno() in self.socketsClient.keys():
                sock.send(buf.encode())
                flg = 0
        except socket.error:
            print("Except send()")
            self.disconnect(sock, flg, self.fdw, self.epoll)

    def broadcast(self, msg, except_sock, sockets):
        for fileno, sock in sockets.items():
            index = -1
            if sockets == self.socketsServer:
                sock, index = sock
            if sock == except_sock:
                continue
            try:
                sock.send(msg)
            except socket.error:
                print("Except send()")
                self.disconnect(sock, index == -1, self.fdw, self.epoll)
                # if index != -1:
                #     self.tree_conn[self.index].remove(index)
                # self.sockets.pop(fileno)
                # sock.close()


    def __init__(self, filename):
        self.try_bind(filename)


    def accept_conn(self, epoll, fdr):
        sock, addr = self.sock.accept()
        # sock.setblocking(0)
        #self.socketsClient[sock.fileno()] = sock
        epoll.register(sock.fileno(), select.EPOLLIN)
        caddr = (addr[0], addr[1] - 1)
        if caddr in self.addrServers:
            index = self.addrServers.index(caddr)
            self.socketsServer[sock.fileno()] = (sock, index)
            self.tree_conn[self.index].append(self.addrServers.index(caddr))
            msg = pickle.dumps(Message('tree', tree=self.tree_conn))
            self.broadcast(msg, self.parentSock, self.socketsServer)
            print('connect Server №%d\n' % index)
            print(self.tree_conn, end='\n\n')
        else:
            self.socketsClient[sock.fileno()] = sock
            print('connect Client ', sock.getpeername())
        self.send_allhist(sock, fdr)


    def disconnect(self, sock, flg, fdw, epoll):
        if flg == 0:
            val = self.socketsClient.pop(sock.fileno())
            epoll.unregister(sock.fileno())
            print("Client (%s, %d) is offline" % val.getpeername())
        elif flg == 1:
            val = self.socketsServer.pop(sock.fileno())
            epoll.unregister(sock.fileno())
            print("Server (%s, %d) is offline" % val[0].getpeername())
            if val[0] == self.parentSock:
                if self.try_connect_parent(epoll) == 0:
                    fdw.close()
                    fdw = open('hist' + str(self.index), 'w')
                print(self.tree_conn, '\n')

            else:
                self.tree_conn[self.index].remove(val[1])
            data = pickle.dumps(Message('tree', tree=self.tree_conn))
            self.broadcast(data, self.parentSock, self.socketsServer)
        return fdw


    def run(self):
        sizeBuf = 1024
        socketsClient = self.socketsClient
        socketsServer = self.socketsServer

        fdw = open('hist' + str(self.index), 'w')
        fdr = open('hist' + str(self.index), 'r')
        self.fdw = fdw
        self.fdr = fdr
        epoll = select.epoll()
        self.epoll = epoll
        epoll.register(self.sock.fileno(), select.EPOLLIN)

        self.try_connect_parent(epoll)

        while 1:
            pairs = epoll.poll()
            for fileno, event in pairs:
                if fileno == self.sock.fileno():
                    self.accept_conn(epoll, fdr)

                elif event & select.EPOLLIN:
                    flg = -1
                    except_sock = None

                    if fileno in socketsClient.keys():
                        sock = socketsClient[fileno]
                        flg = 0
                    elif fileno in socketsServer.keys():
                        sock, index = socketsServer[fileno]
                        except_sock = sock
                        flg = 1
                    try:
                        data = sock.recv(sizeBuf)
                        if data:
                            if flg == 0:
                                msg = Message('msg', msg=data.decode())
                                data = pickle.dumps(msg)
                                print('Recv msg from Client ', sock.getpeername())

                            elif flg == 1:
                                msg = pickle.loads(data)
                                print('Recv msg from Server ', sock.getpeername())

                            else: continue
                            if msg.type == 'msg':
                                self.broadcast(msg.msg.encode(), sock, socketsClient)
                                self.broadcast(data, except_sock, socketsServer)
                                fdw.write(msg.msg)
                                fdw.flush()
                            elif msg.type == 'tree':
                                self.tree_conn.update(msg.tree)
                                data = pickle.dumps(Message('tree', tree=self.tree_conn))
                                self.broadcast(data, except_sock, socketsServer)
                                print(self.tree_conn, '\n')

                        else:
                            #print('NO DATA')
                            fdw = self.disconnect(sock, flg, fdw, epoll)
                            print(self.tree_conn, '\n')


                    except socket.error:
                        print('except socket.error #1')

                elif event & select.EPOLLHUP:
                    print('event & select.EPOLLHUP')
                    if fileno in socketsClient.keys():
                        sock = socketsClient[fileno]
                        flg = 0
                    elif fileno in socketsServer.keys():
                        sock, index = socketsServer[fileno]
                        flg = 1
                    else: continue
                    fdw = self.disconnect(sock, flg, fdw, epoll)
                    print(self.tree_conn, '\n')


if __name__ == '__main__':
    chat = Chat_server('server_list')
    chat.run()

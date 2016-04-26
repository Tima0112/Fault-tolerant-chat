import socket
import select
import sys


def chat_client():
    print('Input name')
    name = sys.stdin.readline() + ': '
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

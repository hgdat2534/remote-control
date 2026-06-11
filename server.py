import socket
import sys

from pyexpat.errors import messages




server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 8080))
server.listen(1)

while True:
    conn, addr = server.accept()
    conn.sendall(b'Hello from server!')
    messages = conn.recv(1024).decode()
    print(messages)

    cmd = input('enter command:')
    while cmd != 'exit':
        conn.sendall(bytes(cmd, 'utf-8'))
        cmd = input('enter command:')




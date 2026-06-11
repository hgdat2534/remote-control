import socket

def take_screenshot():
    print('take screenshot')

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('192.168.1.6', 8080))

client.send(b'Hello from client!')
message = client.recv(1024).decode()
print(message)

cmd = client.recv(1024).decode('utf-8')

while cmd != 'exit':
    if cmd == 'screenshot':
        take_screenshot()
    if cmd == 'quit':
        client.close()
    cmd = client.recv(1024).decode('utf-8')

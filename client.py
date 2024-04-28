from socket import *

IP = "111.18.34.146"
SERVER_PORT = 42310
BUFFLEN = 4096

dataSocket = socket(AF_INET, SOCK_STREAM)

dataSocket.connect((IP, SERVER_PORT))
while True:
    recved = dataSocket.recv(BUFFLEN)
    if recved.decode() == "登录成功!":
        print("登录成功!")
        break
    print(recved.decode())
    tosend = input(">>")
    dataSocket.send(tosend.encode())

while True:

    tosend = input(">> ")
    if tosend == "":
        break

    dataSocket.send(tosend.encode())

    recved = dataSocket.recv(BUFFLEN)

    if not recved:
        break

    print(recved.decode())

dataSocket.close()

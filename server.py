import socket

# 设置服务器的IP地址和端口号
# IP = "172.31.77.104"
IP = "192.168.1.101"
SERVER_PORT = 42310
BUFFLEN = 4096

# 创建socket对象
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 绑定到指定的IP地址和端口号
serverSocket.bind((IP, SERVER_PORT))

# 开始监听传入的连接请求
serverSocket.listen(1)
print("服务器启动，等待客户端连接...")

# 接受一个连接请求
clientSocket, addr = serverSocket.accept()
print(f"连接已建立，客户端地址：{addr}")

# 发送登录成功的消息
clientSocket.send("登录成功!".encode())

# 进入通信阶段
while True:
    # 接收客户端的数据
    data = clientSocket.recv(BUFFLEN)
    if not data:
        break  # 如果没有数据，退出循环
    # 打印接收到的数据
    print(f"收到来自 {addr} 的消息: {data.decode()}")
    # 发送回响应
    clientSocket.send(f"回声: {data.decode()}".encode())

# 关闭连接
clientSocket.close()
serverSocket.close()
print("服务器已关闭。")

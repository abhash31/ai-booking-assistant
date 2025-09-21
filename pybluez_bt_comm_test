import bluetooth

server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("", 1))   # Channel 1
server_sock.listen(1)

print("Waiting for connection...")

client_sock, client_info = server_sock.accept()
print("Accepted connection from", client_info)

try:
    while True:
        data = client_sock.recv(1024)
        if not data:
            break
        print("Received:", data.decode().strip())
except OSError:
    pass

client_sock.close()
server_sock.close()

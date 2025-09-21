#!/usr/bin/env python3
import bluetooth
import threading
import time

class BluetoothServer:
    def __init__(self):
        self.server_sock = None
        self.client_sock = None
        self.running = False
        
    def start_server(self):
        """Start the Bluetooth server"""
        try:
            # Create server socket
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_sock.bind(("", bluetooth.PORT_ANY))
            self.server_sock.listen(1)
            
            # Get the port number
            port = self.server_sock.getsockname()[1]
            
            # UUID for the service (must match Android app)
            uuid = "00001101-0000-1000-8000-00805F9B34FB"
            
            # Advertise service
            bluetooth.advertise_service(self.server_sock, "RPiBluetoothServer",
                                      service_id=uuid,
                                      service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                                      profiles=[bluetooth.SERIAL_PORT_PROFILE])
            
            print(f"Waiting for connection on RFCOMM channel {port}")
            print(f"Service UUID: {uuid}")
            
            # Accept connection
            self.client_sock, client_info = self.server_sock.accept()
            print(f"Connected to {client_info}")
            
            self.running = True
            
            # Start receiving thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
    
    def receive_messages(self):
        """Receive messages from Android device"""
        while self.running:
            try:
                data = self.client_sock.recv(1024).decode('utf-8').strip()
                if data:
                    print(f"Received: {data}")
                    
                    # Handle specific commands
                    if data == "SRT":
                        print("Start command received!")
                        # Add your start logic here
                        self.send_message("SRT_ACK")
                    elif data == "END":
                        print("End command received!")
                        # Add your end logic here
                        self.send_message("END_ACK")
                        
            except bluetooth.BluetoothError:
                print("Connection lost")
                self.running = False
                break
            except Exception as e:
                print(f"Error receiving: {e}")
    
    def send_message(self, message):
        """Send a message to Android device"""
        try:
            if self.client_sock:
                self.client_sock.send(message.encode('utf-8'))
                print(f"Sent: {message}")
                return True
        except Exception as e:
            print(f"Error sending: {e}")
            return False
    
    def close(self):
        """Close all connections"""
        self.running = False
        if self.client_sock:
            self.client_sock.close()
        if self.server_sock:
            self.server_sock.close()
        print("Server closed")

def main():
    server = BluetoothServer()
    
    if server.start_server():
        try:
            # Main loop - you can send messages here
            while server.running:
                cmd = input("Enter command (SRT/END/custom/quit): ").strip()
                if cmd.lower() == "quit":
                    break
                elif cmd:
                    server.send_message(cmd)
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            server.close()
    
if __name__ == "__main__":
    main()

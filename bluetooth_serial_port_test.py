import time
import serial
import threading

# Bluetooth RFCOMM Serial Port
BLUETOOTH_PORT = "/dev/rfcomm0"  # Default RFCOMM port for Bluetooth on Raspberry Pi
BAUD_RATE = 9600  # Baud rate for serial communication

# This function will handle the commands and trigger appropriate actions
def do_action(cmd: str) -> str:
    cmd = cmd.strip().upper()
    if cmd == "START":
        # Start process (replace with your real process logic)
        print(">>> PROCESS STARTED")
        return "ACK START\n"
    elif cmd == "END":
        # End process (replace with your real process logic)
        print(">>> PROCESS ENDED")
        return "ACK END\n"
    else:
        return "ERR UNKNOWN\n"

# Function to send messages to the client over Bluetooth
def send_message(ser, message: str):
    """Send a message to the connected Bluetooth client."""
    ser.write(message.encode('utf-8'))

# Function to handle client connection and both send/receive messages
def handle_client(ser):
    try:
        # Send an initial message to the client
        send_message(ser, "Hello from Raspberry Pi!")

        # Continuously listen for commands from the client
        while True:
            # Read incoming message from the client
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(f"Received command: {line}")
                # Process the command and send response back to the client
                response = do_action(line)
                send_message(ser, response)

                # Send a periodic message every 10 seconds
                time.sleep(10)
                send_message(ser, "MESSAGE FROM RPI")

            else:
                break
    except Exception as e:
        print("Client error:", e)
    finally:
        ser.close()
        print("Client disconnected")

# Main function to set up Bluetooth serial port
def main():
    # Open the Bluetooth serial port
    try:
        ser = serial.Serial(BLUETOOTH_PORT, BAUD_RATE)
        print(f"Bluetooth RFCOMM server running on {BLUETOOTH_PORT}...")
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {BLUETOOTH_PORT}")
        print(str(e))
        return

    # Start the client handler in a separate thread
    client_thread = threading.Thread(target=handle_client, args=(ser,))
    client_thread.start()

    # Keep the server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server interrupted")

if __name__ == "__main__":
    main()

import socket
import struct
import sys

def handle_request(data):
    try:
        print(f"Received raw data: {data}")
        print(f"Data in repr: {repr(data)}")
        print(f"Length of data: {len(data)}")

        # Check if the request is for session initialization
        if b"org.boris.xlloop.Initialize" in data:
            print("Function call: ←org.boris.xlloop.Initialize")
            print("Initializing session...")
            # Return a simple success message (typically a double value like 0.0)
            return struct.pack("<d", 0.0)  # Represents a successful initialization

        # Check for the function name "PYM" in the request data
        elif b"PYM" in data:
            print("Function call: ←PYM")
            # Perform the actual calculation or function execution (example: sum 1, 2, 3)
            result = 42.0  # You can replace this with your actual logic
            return struct.pack("<d", result)  # Return the result as a double
        
        else:
            print("Unknown request")
            return struct.pack("<d", 0.0)  # Respond with 0.0 for unknown requests
    
    except struct.error as e:
        print(f"Error: {e}")
        return struct.pack("<d", 0.0)  # Error fallback

def start_server():
    host, port = "127.0.0.1", 5460
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Python gateway server running on {host}:{port}")

    try:
        while True:
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")
            raw_data = conn.recv(1024)  # Receive the raw data from Excel
            if not raw_data:
                break  # Handle empty data (connection closed by client)
            response = handle_request(raw_data)  # Process the request
            conn.sendall(response)  # Send the response back to Excel
            conn.close()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()
        sys.exit(0)  # Gracefully exit

if __name__ == "__main__":
    start_server()


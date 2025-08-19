import socket  # Main Communication Part-handles the sending and receiving data
import threading  # Handles communication between multiple clients at the same time
import os  # Handles the creation and saving of files
import traceback

HOST = '127.0.0.1'  # Server IP will run on this machine
PORT = 1234  # Port Used for the Chat Room
LISTENER_LIMIT = 5  # Maximum Number of clients that can connect
active_clients = []  # List of all currently connected users


# Helper function to receive exactly n bytes or return None if disconnected
def recv_all(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def listen_for_messages(client, username):  # Function used to listen for messages from Client
    while True:
        try:
            header = client.recv(10).decode('utf-8')  # Determines the type of content it's receiving
            if not header:
                break

            if header == "TEXT_MSG~":  # Check if the content is a Text message
                # Receive 4 bytes length prefix (message size)
                length_bytes = recv_all(client, 4)
                if not length_bytes:
                    break

                message_length = int(length_bytes.decode('utf-8'))

                # Receive the full message according to length
                message_bytes = recv_all(client, message_length)
                if not message_bytes:
                    break

                message = message_bytes.decode('utf-8')

                if message:
                    # PRIVATE MSG: Handle private messages starting with "PRIVATE_MSG~"
                    if message.startswith("PRIVATE_MSG~"):
                        # Format: PRIVATE_MSG~recipient~actual_message
                        try:
                            _, recipient, actual_message = message.split('~', 2)
                        except ValueError:
                            print(f"Malformed private message from {username}: {message}")
                            continue

                        # Find recipient socket
                        recipient_client = None
                        for user, client_socket in active_clients:
                            if user == recipient:
                                recipient_client = client_socket
                                break

                        if recipient_client:
                            # Send message to recipient only
                            private_msg = f"{username} (private)~{actual_message}"
                            send_message_to_client(recipient_client, private_msg)
                            # Optionally, also send back to sender for confirmation:
                            send_message_to_client(client, f"You (to {recipient})~{actual_message}")
                        else:
                            # Recipient not found — notify sender
                            send_message_to_client(client, f"SERVER~User '{recipient}' not found or offline.")
                    else:
                        # Broadcast message to all users
                        final_msg = username + '~' + message
                        send_messages_to_all(final_msg)  # Shows Message to everyone(CLIENTS)
                else:
                    print(f"The message sent from client {username} is empty")

            elif header == "FILE_SEND":
                # 1. Receive filename size first (fixed 4-byte length)
                filename_size = int(client.recv(4).decode('utf-8'))

                # 2. Receiving the Filename
                filename = client.recv(filename_size).decode('utf-8')

                filesize = int(client.recv(16).decode('utf-8'))  # 3.File size in bytes

                # 4. Receives the file data in chunks until all the data is downloaded
                file_data = b''
                while len(file_data) < filesize:
                    chunk = client.recv(1024)
                    if not chunk:
                        break
                    file_data += chunk

                # Creates a folder for the downloaded file and puts in the local disk
                save_path = os.path.join("received_files", filename)
                os.makedirs("received_files", exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(file_data)

                # Notifies all of the users that the file has been sent
                print(f"[{username}] sent file: {filename} ({filesize} bytes)")
                send_messages_to_all(f"SERVER~{username} sent a file: {filename}")

            # When it receives an unexpected header
            else:
                print(f"Unknown header received: {header}")

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            break


# Function to send message to a single client
def send_message_to_client(client, message):
    try:
        client.sendall(message.encode())
    except Exception:
        # Client likely disconnected, remove from active_clients
        for user in active_clients:
            if user[1] == client:
                active_clients.remove(user)
                break


# Function to send any new message to all the clients that are currently connected to this server
def send_messages_to_all(message):
    for user in active_clients:
        send_message_to_client(user[1], message)


# Function to handle client
def client_handler(client):
    # Server will listen for client message that will Contain the username
    while True:
        username = client.recv(2048).decode('utf-8')  # Receives Username from client
        if username != '':
            active_clients.append((username, client))
            # Notifies that a new user has joined
            prompt_message = "SERVER~" + f"{username} added to the chat"
            send_messages_to_all(prompt_message)
            break
        else:
            print("Client username is empty")

    # Starts a thread that keeps checking the clients messages
    threading.Thread(target=listen_for_messages, args=(client, username,)).start()


# Main starts the chat server
def main():
    # Creating the socket object
    # AF_INET: uses IPv4 addresses
    # SOCK_STREAM: uses TCP for communication
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Creating a try catch block
    try:
        # Provide the server with an address in the form of host IP and port
        server.bind((HOST, PORT))
        print(f"Running the server on {HOST} {PORT}")
    except:
        print(f"Unable to bind to host {HOST} and port {PORT}")

    # Set server limit
    server.listen(LISTENER_LIMIT)

    # This while loop will keep listening to client connections
    while True:
        client, address = server.accept()
        print(f"Successfully connected to client {address[0]} {address[1]}")

        threading.Thread(target=client_handler, args=(client,)).start()


# Run main function only if the script is rightly executed
if __name__ == '__main__':
    main()

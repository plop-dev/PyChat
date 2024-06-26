import socket
from threading import Thread
import datetime

MESSAGES = []

# server's IP address
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 35875  # port we want to use
separator_token = "<SEP>"  # we will use this to separate the client name & message

# initialize list/set of all connected client's sockets
client_sockets = list()
# create a TCP socket
s = socket.socket()
# make the port as reusable port
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# bind the socket to the address we specified
try:
    s.bind((SERVER_HOST, SERVER_PORT))
except socket.error as e:
    print(f"Error: Failed to bind socket: {e}")
    exit(1)
# listen for upcoming connections
s.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")


def listen_for_client(cs: socket.socket):
    """
    This function keep listening for a message from `cs` socket
    Whenever a message is received, broadcast it to all other connected clients
    """
    while True:
        try:
            # keep listening for a message from `cs` socket
            msg = cs.recv(1024).decode()
        except Exception as e:
            # client no longer connected
            # remove it from the set
            print(f"[!] Error: {e}")
            for client_socketd in client_sockets:
                if client_socketd['socket'] == cs:
                    client_sockets.remove(client_socketd)
            break  # Exit the loop if an error occurs
        else:
            if not msg:
                # If no message received, client disconnected
                print(f"[-] Client {cs.getpeername()} disconnected.")
                for client_socketd in client_sockets:
                    if client_socketd['socket'] == cs:
                        client_sockets.remove(client_socketd)
                break  # Exit the loop if no message received
            elif msg.__contains__('<S>disconnect'):
                time_now = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

                for client_socketd in client_sockets:
                    if client_socketd['socket'] == cs:
                        client_socketd['last_online'] = time_now
            elif msg.__contains__('<S>connect'):
                for client_socketd in client_sockets:
                    if client_socketd['socket'] == cs:
                        client_socketd['last_online'] = "now"
            elif msg.__contains__('<H>'):
                for client_socketd in client_sockets:
                    if client_socketd['socket'] == cs:
                        client_socketd['username'] = msg.replace('<H>', '')
            else:
                msg = msg.replace(separator_token, ": ")

        # iterate over all connected sockets
        for client_socketd in client_sockets:
            # and send the message
            try:
                client_socket = client_socketd['socket']
                client_socket.send(msg.encode())
                if not msg.__contains__('<H>') and not msg.__contains__('<S>'):
                    date = msg.split('|')[0]
                    sender = msg.split('|')[1]
                    message = msg.split('|')[2]
                    MESSAGES.append({"date": date, "sender": sender, "message": message})
            except Exception as e:
                print(f"[!] Error sending message to client: {e}")


while True:
    # we keep listening for new connections all the time
    try:
        client_socket, client_address = s.accept()
    except Exception as e:
        print(f"[!] Error accepting connection: {e}")
        continue  # Continue to the next iteration if an error occurs

    
    print(f"[+] {client_address} connected.")
    # add the new connected client to connected sockets
    time_now = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    client_sockets.append({"socket": client_socket, "last_online": time_now})
    # start a new thread that listens for each client's messages
    t = Thread(target=listen_for_client, args=(client_socket,))
    # make the thread daemon so it ends whenever the main thread ends
    t.daemon = True
    # start the thread
    t.start()

# close client sockets
for cs in client_sockets:
    cs.close()
# close server socket
s.close()

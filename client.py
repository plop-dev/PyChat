import socket
import random
from threading import Thread
from datetime import datetime

# choose a random color for the client
client_color = random.choice(colors)

# server's IP address
# if the server is not on this machine, 
# put the private (network) IP address (e.g 192.168.1.2)
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 35875 # server's port
separator_token = "<SEP>" # we will use this to separate the client name & message

# initialize TCP socket
s = socket.socket()
print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}...")
# connect to the server
s.connect((SERVER_HOST, SERVER_PORT))
print("[+] Connected.")
# prompt the client for a name
name = input("Enter your name: ")

def listen_for_messages():
    while True:
        messageRAW = s.recv(1024).decode()

def send(to_send):
    time_now = datetime.now().strftime('%H:%M:%S')
    to_send = f"{time_now}|{name}|{to_send}"
    # finally, send the message
    s.send(to_send.encode())

while True:
    # input message we want to send to the server
    to_send = input()
    # a way to exit the program
    if to_send.lower() == 'quit':
        break
    elif to_send.lower().strip() != '':
        send(to_send)

s.close()

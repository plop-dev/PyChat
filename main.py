from typing import Type
from textual.app import App, ComposeResult
from textual.driver import Driver
from textual.events import Key
from textual.widget import Widget
from textual.widgets import Header, Footer, Button, Static, Input, Label, RichLog
from textual.suggester import Suggester
from textual.containers import Container, Horizontal, VerticalScroll, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.worker import Worker, get_current_worker
from textual import events, on, binding, work
import datetime
import time
import socket
import random
from threading import Thread
from datetime import datetime

SENDER = "plop"
DEST = "Eny"
COLOUR = "#42d667"
MESSAGES = []

SERVER_HOST = "localhost"
SERVER_PORT = 35875 # server's port

class AutoSuggest(Suggester):
    async def get_suggestion(self, value: str) -> str | None:
        keywords = ['plop', 'lumyx']
        try:
            for keyword in keywords:
                for i in range(0, len(value)):
                    if keyword[i] == value[i]:
                        return keyword
        except:
            pass
        return None
    
class Message(Widget):
    time_now = reactive('')
    sender = reactive('')
    message_content = reactive('')
    
    def compose(self):
        with Horizontal(classes="message"):
            yield Label(f"[bold {COLOUR}]{self.sender}[/]\n{self.message_content}", classes='message-content')
            yield Label(f"[bold #727872]{self.time_now}[/]", classes='message-date')

class ServerMessage(Widget):
    def __init__(self, message: str):
        self.message = message
        super().__init__()
    
    def compose(self):
        with Horizontal(classes="server-message"):
            yield Label(f"[bold]{self.message}[/]", classes='server-message-content')
            
class ChatApp(App):
    BINDINGS = [
        binding.Binding("ctrl+q, ctrl+c", "quit_app", priority=True)
    ]
    ENABLE_COMMAND_PALETTE = False
    CSS = """
        #status {
            dock: top;
            height: auto;
            border-bottom: solid grey;
            padding-top: 1;
        }
        #message_container {
            margin: 1 2;
        }
        #inputs {
            height: 5;
            dock: bottom;
            padding-bottom: 1;
        }
        
        .status {
            align: center top;
        }
        #user_status {
            text-align: center;   
        }
        #text_input {
            width: 80%;
            dock: bottom;
        }
        #send_button {
            margin-right: 4;
            dock: bottom;
            align: right middle;
        }
        
        #message-container {
            height: auto;
            padding: 0 1;
        }
        
        Message {
            height: 3;
            width: 1fr;
        }
        .message {
            height: 3;
            width: 1fr;
            
            .message-content {
                width: 1fr;
            }
            .message-date {
                dock: right;
            }
        }
        ServerMessage {
            height: 1;
            width: 1fr;
        }
        .server-message {
            align-horizontal: center;
            height: 1;
            width: 1fr;
            
            .server-message-content {
                height: 1;
                content-align-vertical: middle;
            }
        }
    """
    
    def compose(self) -> ComposeResult:
        yield Footer()
        yield Container(
            Label(f"{DEST}: [bold #50dc50]Online[/]\n[bold #727872]Last Online:[/] [normal grey]Now[/]", id='user_status'),
            id='status',
            classes='status'
        )
        yield VerticalScroll(id="message-container")
        yield Container(
            Horizontal(
                Input(placeholder="Message", suggester=AutoSuggest(case_sensitive=False), id='text_input'),
                Button("Send", variant='primary', id='send_button'),
                classes='inputs'
            ),
            id='inputs',
        )
    
    
    def on_mount(self):
        self.query_one('#text_input', Input).focus()
        
        self.s = socket.socket()
        self.new_server_message(f"[yellow]Connecting to {SERVER_HOST}:{SERVER_PORT}...[/]")
        try:
            self.s.connect((SERVER_HOST, SERVER_PORT))
        except:
            self.new_server_message(f"[#bd453c]Failed to connect. Check the server is online.[/]")
        else:
            self.s.send(f"<H>{SENDER}".encode())
            self.s.send(f"<S>connect|{SENDER}".encode())
            self.new_server_message(f"[#42d667]Connected.[/]")
        
        self.listen_for_messages(self.s)
        
    @work(exclusive=True, thread=True)
    def listen_for_messages(self, s):
        worker = get_current_worker()
        while True:
            messageRAW = s.recv(1024).decode()
            
            if messageRAW.__contains__('<S>'):
                time_now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                
                if messageRAW.__contains__('disconnect'):
                    username = messageRAW.split('<S>disconnect|')[1]
                    self.call_from_thread(self.update_user_status, time_now, "Offline")
                    self.call_from_thread(self.new_server_message, f"{username} has left the chat")
                    continue
                elif messageRAW.__contains__('connect'):
                    username = messageRAW.split('<S>connect|')[1]
                    self.call_from_thread(self.update_user_status, "Now", "Online")
                    self.call_from_thread(self.new_server_message, f"{username} has joined the chat")
                    continue
            elif messageRAW.__contains__('<H>'):
                continue
            else:
                date = messageRAW.split('|')[0]
                sender = messageRAW.split('|')[1]
                message = messageRAW.split('|')[2]
                
                if sender == SENDER:
                    continue
                elif not worker.is_cancelled:
                    self.call_from_thread(self.new_message, message, sender, date)
                    # self.new_message(message, sender, date)
    
    
    def new_server_message(self, message: str):
        msg_container = self.query_one('#message-container')
        new_server_message = ServerMessage(message)
        msg_container.mount(new_server_message)
        new_server_message.scroll_visible()
    
    def new_message(self, message: str, sender: str, date: str):
        msg_container = self.query_one('#message-container')
        new_message = Message()
        msg_container.mount(new_message)
        new_message.scroll_visible()
        
        new_message.message_content = message
        new_message.time_now = date
        new_message.sender = sender
    
    def action_quit_app(self):
        self.s.send(f"<S>disconnect|{SENDER}".encode())
        self.s.close()
        self.workers.cancel_all()
        self.action_quit()
        self.exit()
    
    def update_user_status(self, time: str, status: str) -> None:
        if status == "Online":
            status_colour = "#959595"
        elif status == "Offline":
            status_colour = "#50dc50"
        
        self.query_one('#user_status').update(f"{DEST}: [bold {status_colour}]{status}[/]\n[bold #727872]Last Online:[/] [normal grey]{time}[/]")
    
    @on(Button.Pressed, '#send_button')
    def send_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one('#text_input', Input).action_submit()
        self.query_one('#text_input', Input).focus()
        
    @on(Input.Submitted, '#text_input')
    def message_submitted(self, event: Input.Submitted) -> None:
        time_now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        self.new_message(event.value, SENDER, time_now)
        self.s.send(f"{time_now}|{SENDER}|{event.value}".encode())
        event.input.clear()


app = ChatApp()
app.run()

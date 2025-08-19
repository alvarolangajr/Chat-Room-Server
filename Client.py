# import required modules
import socket #Main Communication Part-handles the sending and receiveing data
import threading #Handles communication between multiple clients at the same time
import tkinter as tk #Python Library for GUIs
from tkinter import scrolledtext #Gives the possibility to scroll
from tkinter import messagebox #Displays messages and errors(if they occur)
from tkinter import filedialog #Opening and Saving Files
from tkinter import simpledialog # For input dialogs (CONTACTS)
import os  # Required for file operations
import json # For saving/loading contacts (CONTACTS)

HOST = '127.0.0.1' #Server IP will run on this machine
PORT = 1234 # Port Used for the Chat Room

# Updated color to your custom background color
CUSTOM_BLUE = '#165ACD' #Background for Buttons
OCEAN_BLUE = '#464EB8' #Buttons and borders
WHITE = "white" #Background and Text
FONT = ("Times New Roman", 17) #Main Font for Messages
BUTTON_FONT = ("Times New Roman", 15) #Fonts on the Buttons
SMALL_FONT = ("Times New Roman", 13) #Fonts for Smaller/Less Important texts

CONTACTS_FILE = "contacts.json" # CONTACTS: filename to save contacts

# Creating a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def add_message(message): #Enables the box for messages
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END, message + '\n')
    message_box.config(state=tk.DISABLED)
    message_box.see(tk.END)  # Scroll to the end

def connect(): #Connects to Server and starts the thread
    try:
        client.connect((HOST, PORT))
        print("Successfully connected to server")
        add_message("[SERVER] Successfully connected to the server")
    except:
        messagebox.showerror("Unable to connect to server", f"Unable to connect to server {HOST} {PORT}")
        return

    username = username_textbox.get()
    if username != '':
        client.sendall(username.encode())
    else:
        messagebox.showerror("Invalid username", "Username cannot be empty")
        return

    #The thread that was mentioned prior, this is used to check/listen for upcoming messages
    threading.Thread(target=listen_for_messages_from_server, args=(client,), daemon=True).start()

    #Disable username input after the connection is sucessful
    username_textbox.config(state=tk.DISABLED)
    username_button.config(state=tk.DISABLED)

def send_message(): #Sends a text message to the server
    message = message_textbox.get()
    if message == '':
        messagebox.showerror("Empty message", "Message cannot be empty")
        return

    # CONTACTS: get selected contact to send private message to
    selected_contacts = contacts_listbox.curselection()
    if not selected_contacts:
        messagebox.showerror("No Contact Selected", "Please select a contact to send the message.")
        return

    recipient = contacts_listbox.get(selected_contacts[0])

    # For demonstration, send message with a header "PRIVATE_MSG~recipient~message"
    # You may want to change this to your actual protocol and update server accordingly

    # Construct the message string with recipient
    full_message = f"PRIVATE_MSG~{recipient}~{message}"

    try:
        # Send the 10-byte header first
        client.sendall("TEXT_MSG~".encode('utf-8'))  # 10-byte header (no extra space)

        # Prepare full_message bytes and length prefix (4 bytes)
        message_bytes = full_message.encode('utf-8')
        message_length_str = f"{len(message_bytes):04}"  # 4-byte length string, zero-padded

        # Send the length prefix
        client.sendall(message_length_str.encode('utf-8'))

        # Then send the actual message bytes
        client.sendall(message_bytes)

        # Show sent message locally
        add_message(f"[You -> {recipient}] {message}")

        # Clear message box
        message_textbox.delete(0, tk.END)
    except Exception as e:
        messagebox.showerror("Send Failed", str(e))

def send_file(): #Opens the file dialog(popup window that lets the user browse the files),reads file and sends it to server
    file_path = filedialog.askopenfilename()
    if not file_path:
        return  # User cancelled

    try:
        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)

        #Inform server that the file transfer is starting
        client.send("FILE_SEND".encode('utf-8'))  # Tag the message as a file
        client.send(f"{len(filename):04}".encode('utf-8'))  # Filename length
        client.send(filename.encode('utf-8'))  # Filename
        client.send(f"{filesize:016}".encode('utf-8'))  # File size

        #Send file data in chunks
        with open(file_path, 'rb') as f:
            while chunk := f.read(1024):
                client.send(chunk)

        add_message(f"[You] Sent file: {filename}")
    except Exception as e:
        messagebox.showerror("File Transfer Failed", str(e))

# CONTACTS: Load contacts from file
def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, 'r') as f:
                contacts = json.load(f)
                for contact in contacts:
                    contacts_listbox.insert(tk.END, contact)
        except:
            pass  # Fail silently if bad file

# CONTACTS: Save contacts to file
def save_contacts():
    contacts = contacts_listbox.get(0, tk.END)
    try:
        with open(CONTACTS_FILE, 'w') as f:
            json.dump(contacts, f)
    except Exception as e:
        messagebox.showerror("Save Contacts Failed", str(e))

# CONTACTS: Add a contact from input dialog
def add_contact():
    new_contact = simpledialog.askstring("Add Contact", "Enter contact username:")
    if new_contact:
        if new_contact in contacts_listbox.get(0, tk.END):
            messagebox.showerror("Duplicate Contact", "This contact already exists.")
            return
        contacts_listbox.insert(tk.END, new_contact)
        save_contacts()

# CONTACTS: Remove selected contact
def remove_contact():
    selected = contacts_listbox.curselection()
    if selected:
        contacts_listbox.delete(selected)
        save_contacts()
    else:
        messagebox.showerror("No Contact Selected", "Please select a contact to remove.")

# Creating main GUI window
root = tk.Tk()
root.geometry("800x620") #WindowSize (Adjusted width to fit contacts panel)
root.title("Chat Room")
root.resizable(False, False) #prevents the user from editing the edges

# Grid configuration
root.grid_rowconfigure(0, weight=1) #Username Area
root.grid_rowconfigure(1, weight=8) #Largest Space-Chat Area
root.grid_rowconfigure(2, weight=1) #Input/buttons

root.grid_columnconfigure(0, weight=4)  # Main chat area
root.grid_columnconfigure(1, weight=1)  # Contacts panel

# Edits the Username Area
top_frame = tk.Frame(root, width=650, height=100, bg=CUSTOM_BLUE)
top_frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)
top_frame.grid_propagate(False) #Tells the library(Tkinter) to obey the dimensions given

# Edits the messages area
middle_frame = tk.Frame(root, width=650, height=350, bg=CUSTOM_BLUE)
middle_frame.grid(row=1, column=0, sticky=tk.NSEW)
middle_frame.grid_propagate(False) #Tells the library(Tkinter) to obey the dimensions gave

# CONTACTS: Contacts panel on right side
contacts_frame = tk.Frame(root, width=150, height=350, bg=CUSTOM_BLUE)
contacts_frame.grid(row=1, column=1, sticky=tk.NSEW)
contacts_frame.grid_propagate(False)

contacts_label = tk.Label(contacts_frame, text="Contacts", font=FONT, bg=CUSTOM_BLUE, fg=WHITE)
contacts_label.pack(pady=5)

contacts_listbox = tk.Listbox(contacts_frame, font=SMALL_FONT, bg='white', fg='black', height=20)
contacts_listbox.pack(fill=tk.BOTH, expand=True, padx=5)

contacts_buttons_frame = tk.Frame(contacts_frame, bg=CUSTOM_BLUE)
contacts_buttons_frame.pack(pady=5, fill=tk.X)

add_button = tk.Button(contacts_buttons_frame, text="Add", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE, command=add_contact)
add_button.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

remove_button = tk.Button(contacts_buttons_frame, text="Remove", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE, command=remove_contact)
remove_button.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

# Edits the message entry and buttons
bottom_frame = tk.Frame(root, width=650, height=150, bg=CUSTOM_BLUE)
bottom_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)
bottom_frame.grid_propagate(False) #Tells the library(Tkinter) to obey the dimensions gave

# Edit "Enter Username"
username_label = tk.Label(top_frame, text="Enter username:", font=FONT, bg=CUSTOM_BLUE, fg=WHITE)
username_label.pack(side=tk.LEFT, padx=10)

# Text box for entering Username
username_textbox = tk.Entry(top_frame, font=FONT, bg='white', fg='black', width=23)
username_textbox.pack(side=tk.LEFT)

# "Join" button for entering Usernmae
username_button = tk.Button(top_frame, text="Join", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE, command=connect)
username_button.pack(side=tk.LEFT, padx=15)

# Where the message is typed
message_textbox = tk.Entry(bottom_frame, font=FONT, bg='white', fg='black', width=40)
message_textbox.pack(side=tk.LEFT, padx=10)

# "Send" BUTTON
message_button = tk.Button(bottom_frame, text="Send", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE, command=send_message)
message_button.pack(side=tk.LEFT, padx=10)

# "Send File" button to send file
file_button = tk.Button(bottom_frame, text="Send File", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE, command=send_file)
file_button.pack(side=tk.LEFT, padx=10)

# Message Display Box
message_box = scrolledtext.ScrolledText(middle_frame, font=SMALL_FONT, bg='white', fg='black', width=50, height=30)
message_box.config(state=tk.DISABLED)
message_box.pack(side=tk.TOP)

def listen_for_messages_from_server(client):
    while 1:
        try:
            #Receive message from server
            message = client.recv(2048).decode('utf-8')
            if message != '':
                username = message.split("~")[0]
                content = message.split('~')[1]

                #Display message in the chat window
                add_message(f"[{username}] {content}")
            else:
                messagebox.showerror("Error", "Message received from server is empty")
        except:
            #Show error if connection to server is lost
            messagebox.showerror("Connection Error", "Lost connection to the server.")
            break

# Load contacts on start
load_contacts()

# Runs the main GUI loop to display the window
root.mainloop()

import socket       # provides low-level networking interface
import threading    # allows for multi-threading
import os           # provides functions for interacting with the operating system
import logging      # used to log messages for a library or application
import sqlite3      # DB-API 2.0 interface for SQLite database
import datetime     # supplies classes for manipulating dates and times

# set host and port for server, ==  to enviroment variables, or otherwise default: HOST:localhost, PORT:8888
HOST = os.getenv("Host", "localhost")
PORT = int(os.getenv("PORT", 8888))

# set basic config for logging, write logs to: "server.log", logging level set to: INFO
logging.basicConfig(filename = "server.log", level = logging.INFO)

# establish connection to SQLite db: "client_requests.db", create curser object for SQL execution commands
conn = sqlite3.connect("client_requests.db")
c = conn.cursor()
# execute SQL command to create table "requests", if not existing. Three columns: "id", "client_address", "request_time"
# after (any) changes, connection is closed
c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY,
        client_address TEXT,
        request_time TEXT
        )
    """)
conn.commit()
conn.close()

# defines function "handle_client", takes two arguments: "client_connection", "client_address"
def handle_client(client_connection, client_address):
    
    # establish connection to SQLite database
    conn = sqlite3.connect("client_requests.db")
    c = conn.cursor()   # creates curser object which can execute SQL comands
    
    try:    # starts a try block, exceptions will be handled by except block
        request_data = client_connection.recv(1024)     # recives data from client; ".recv" method takes one arg; max data to be recived at once: 1024 bytes
        print(request_data.decode("utf-8"))     # takes recived data, decodes it to a string using UTF-8 encoding; then prints
        
        # response to be sent to client; byte string that includes HTTP status code "200 OK"; content type: "(text/plain)"; body response: "Hello, World!"
        http_response = b"""HTTP/1.1 200 OK \r\nContent-Type: text/plain\r\n\r\nHello, World!\n"""
        
        client_connection.sendall(http_response)    # sends response
        
        now = datetime.datetime.now()   # get current date & time (realtime)
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]   # format datetime: "YYYY-MM-DD ; HH:MM:SS.ss"       normally 6 places right of decimal, set to only display 2
        
        # logs informational message including client's: address, and time request was recived
        logging.info(f"Received request from {client_address}. Time: {formatted_now}")
        
        # SQL command to insert a new row into "requests table" with logging information
        c.execute("INSERT INTO requests (client_address, request_time) VALUES (?, ?)", (str(client_address), formatted_now))
        conn.commit()   # commits current transaction
        
    except Exception as e:  # catches exceptions raised in try block
        logging.error(f"Error: {e}")    # logs error message that includes exception
    finally:    # executed no matter what
        client_connection.close()   # closes connection to client
        conn.close()    # closes connection to the database

# creates new socket object; ".AF_INET" specifies use to be Internet address family; SOCK_STREAM specifies socket use TCP protocal        
listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sets socket option to 1, which allows socket to reuse same address; useful to avoid "address already in ues" error that can occur when trying to restart server after being shut down
listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# binds socket to specific network interface and port number; defined above
listen_socket.bind((HOST, PORT))
# listen for incoming connections; 1 specifies max number of queued connections
listen_socket.listen(1)

# prints that server is running and listening for connections on specified port
print(f"Serving HTTP on port {PORT} ...")

try: # starts try block, exceptions will be handled by except block
    while True: # starts infinite loop
        client_connection, client_address = listen_socket.accept()  # waites for client to connect to server; when client connects, returns new socket object representing connection & client address
        threading.Thread(target = handle_client, args=(client_connection, client_address)).start()  # creates new thread for each client that connects; target arg is function that thread will execute ("handle_client"); args argument returns tuple of arguments to pass functtion ("client_connection", "client_address")
except KeyboardInterrupt:
    print("\nShutting down...") # catches exception: when user presses Ctrl+C to stop server; then prints as such
finally:    # executed no matter what
    listen_socket.close()   # closes listing socket

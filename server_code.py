import socket       
import threading               
import logging           
import datetime 
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

HOST = os.getenv("host", "localhost")
PORT = int(os.getenv("port", 8888))

logging.basicConfig(filename = "server.log", level = logging.INFO)

def create_table():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    c = conn.cursor()
    c.execute("""
            CREATE TABLE IF NOT EXISTS requests (
            id SERIAL PRIMARY KEY,
            client_address TEXT,
            request_time TEXT
            )
        """)
    conn.commit()
    conn.close()

create_table()

def handle_client(client_connection, client_address):
    
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    c = conn.cursor()
    
    try:
        request_data = client_connection.recv(1024)
        print(request_data.decode("utf-8"))
        
        http_response = b"""HTTP/1.1 200 OK \r\nContent-Type: text/plain\r\n\r\nHello, World!\n"""
        
        client_connection.sendall(http_response)
        
        now = datetime.datetime.now()
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
        
        logging.info(f"Received request from {client_address}. Time: {formatted_now}")
        
        c.execute("INSERT INTO requests (client_address, request_time) VALUES (%s, %s)", (str(client_address), formatted_now))
        conn.commit()
        
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        client_connection.close()
        conn.close()

listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen_socket.bind((HOST, PORT))
listen_socket.listen(1)

print(f"Serving HTTP on port {PORT} ...")

try:
    while True:
        client_connection, client_address = listen_socket.accept()
        threading.Thread(target = handle_client, args=(client_connection, client_address)).start()
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    listen_socket.close()

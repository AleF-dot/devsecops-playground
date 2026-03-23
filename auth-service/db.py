import psycopg2
from psycopg2 import OperationalError
import time

def get_connection():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host="postgres-auth",
                database="authdb",
                user="auth",
                password="auth123"
            )
            return conn
        except OperationalError as e:
            print(f"Connection error: {e}")
            retries -= 1
            print(f"Retry... Left:{retries}")
            time.sleep(3)
    raise Exception("Connection failed")

def init_db(conn):
    cur = conn.cursor()
    
    create_users_table = '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(15) NOT NULL UNIQUE,
            password  VARCHAR(15) NOT NULL,
            status VARCHAR NOT NULL
        )
        '''
    
    create_sessions_table = '''
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            token VARCHAR(30) NOT NULL UNIQUE,
            username  VARCHAR(15) NOT NULL,
            creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
    
    create_attempts_table = '''
        CREATE TABLE IF NOT EXISTS attempts (
            id SERIAL PRIMARY KEY,
            username  VARCHAR(15) NOT NULL UNIQUE,
            attempts INTEGER
        )
        '''

    cur.execute(create_users_table)
    cur.execute(create_sessions_table)
    cur.execute(create_attempts_table)
    
    cur.execute("INSERT INTO users (username, password, status) VALUES ('admin', 'secret', 'active') ON CONFLICT (username) DO NOTHING")

    conn.commit()    
    cur.close()



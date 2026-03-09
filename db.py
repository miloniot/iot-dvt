import mysql.connector
from dotenv import load_dotenv
import os

# Load the database credentials from the .env file
load_dotenv()

# This function creates and returns a connection to the database
def get_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    return connection

# This function creates all the tables we need in the database
def create_tables():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Table to store registered users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARBINARY(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table to store IoT devices added by users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                manufacturer VARCHAR(100) NOT NULL,
                model VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Table to store vulnerabilities found for each device
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                device_id INT NOT NULL,
                cve_id VARCHAR(50) NOT NULL,
                description TEXT,
                severity VARCHAR(20),
                plain_summary TEXT,
                recommendation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
            )
        """)

        # Table to store SUS questionnaire results
        # user_id is stored to prevent duplicate submissions
        # but participant_number is shown to admin — not the username
        # This ensures anonymity even for the admin
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sus_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                participant_number INT NOT NULL,
                q1 INT NOT NULL,
                q2 INT NOT NULL,
                q3 INT NOT NULL,
                q4 INT NOT NULL,
                q5 INT NOT NULL,
                q6 INT NOT NULL,
                q7 INT NOT NULL,
                q8 INT NOT NULL,
                q9 INT NOT NULL,
                q10 INT NOT NULL,
                sus_score FLOAT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("Tables created successfully!")

    except Exception as e:
        print(f"Error creating tables: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Run this file directly to create the tables
if __name__ == "__main__":
    create_tables()
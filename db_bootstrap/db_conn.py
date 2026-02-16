import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="achalla",
        database="robodynamics_db",
        charset="utf8mb4",
        use_unicode=True,
        autocommit=True
    )

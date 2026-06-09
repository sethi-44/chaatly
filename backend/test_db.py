from app.database import engine

try:
    connection = engine.connect()
    print("Connected successfully!")
    connection.close()
except Exception as e:
    print("Error:", e)
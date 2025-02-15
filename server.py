from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import uvicorn

app = FastAPI()

# Database connection settings
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "numberplate",
    "port": 3306
}

# Pydantic model for request body
class NumberPlate(BaseModel):
    plate: str

# Function to initialize the database
def init_db():
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            port=DB_CONFIG["port"]
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        connection.database = DB_CONFIG['database']
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS numberplate (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numberplate TEXT NOT NULL,
                entry_date DATE,
                entry_time TIME
            )
        ''')
        connection.commit()
        cursor.close()
        connection.close()
    except Error as e:
        print(f"Database initialization error: {e}")

# Initialize the database on startup
init_db()

@app.post("/store_plate/")
def store_plate(data: NumberPlate):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        insert_query = "INSERT INTO numberplate (numberplate, entry_date, entry_time) VALUES (%s, %s, %s)"
        current_date = datetime.now().date()
        current_time = datetime.now().time()
        cursor.execute(insert_query, (data.plate, current_date, current_time))
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "Number plate stored successfully!"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/plates/")
def get_plates():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SELECT id, numberplate, entry_date, entry_time FROM numberplate")
        plates = cursor.fetchall()

        # Convert MySQL data to a properly formatted response
        formatted_plates = []
        for plate in plates:
            formatted_plates.append({
                "id": plate[0],
                "numberplate": plate[1],
                "entry_date": str(plate[2]),  # Convert DATE to string
                "entry_time": str(plate[3])   # Convert TIME to string (ensures JSON compatibility)
            })

        cursor.close()
        connection.close()
        return {"plates": formatted_plates}
    
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
<<<<<<< HEAD
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import time  # Import time module for measuring execution time

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MySQL Database Connection Pooling
def get_mysql_connection():
    try:
        start_db_time = time.time()  # Start DB connection timer
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345",
            database="alerts",
        )
        db_time_taken = time.time() - start_db_time  # End DB connection timer
        return connection, db_time_taken
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None, None

@app.get("/analytics/get_voltage_data")
def get_voltage_data(filter: str):
    total_start_time = time.time()  # Start total time measurement
    
    try:
        # Measure DB connection time
        mydb, db_time_taken = get_mysql_connection()
        if not mydb:
            return JSONResponse(content={"error": "Database connection failed"}, status_code=500)

        mycursor = mydb.cursor()

        now = datetime.now()

        # Define integer-based time intervals
        if filter == "2hr":
            start_time = now - timedelta(hours=2)
            interval = 60  # No aggregation
        elif filter == "1day":
            start_time = now - timedelta(days=1)
            interval = 300  # 5 minutes
        elif filter == "1week":
            start_time = now - timedelta(weeks=1)
            interval = 900  # 15 minutes
        elif filter == "1month":
            start_time = now - timedelta(days=30)
            interval = 3600  # 1 hour
        elif filter == "3month":
            start_time = now - timedelta(days=90)
            interval = 3600  # 3 hours
        else:
            return JSONResponse(content={"error": "Invalid filter."}, status_code=400)

        # Measure query execution time
        query_start_time = time.time()

        query = f"""
        SELECT 
            MIN(deviceTimestamp) AS deviceTimestamp,  
            AVG(R) AS R
        FROM analytics
        WHERE location = 'Substation 15' and bayNumber = 2 and type = 'transformer'  and parameter = 'Current' and  deviceTimestamp >= %s
        GROUP BY UNIX_TIMESTAMP(deviceTimestamp) DIV {interval}
        ORDER BY deviceTimestamp ASC
        """
        
        mycursor.execute(query, (start_time,))
        values = mycursor.fetchall()

        query_time_taken = time.time() - query_start_time  # End query execution timer

        # Measure data processing time
        processing_start_time = time.time()

        df = pd.DataFrame(values, columns=["deviceTimestamp", "R"])

        # Ignore null values instead of filling with 0
        df = df.dropna(subset=["R"])
        df["R"] = pd.to_numeric(df["R"], errors="coerce").astype(float)
        df["deviceTimestamp"] = df["deviceTimestamp"].astype(str)

        json_data = df.to_dict(orient="records")

        data_processing_time_taken = time.time() - processing_start_time  # End processing timer

        # Close cursor and DB connection
        mycursor.close()
        mydb.close()

        total_time_taken = time.time() - total_start_time  # End total time measurement

        return JSONResponse(content={
            "data": json_data,
            "timing": {
                "total_time_seconds": total_time_taken,
                "db_connection_seconds": db_time_taken,
                "query_execution_seconds": query_time_taken,
                "data_processing_seconds": data_processing_time_taken
            }
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8200, reload=True)
=======
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import time
import json
from decimal import Decimal

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Connection Function
def get_mysql_connection():
    try:
        start_db_time = time.time()
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345",
            database="alerts",
        )
        return connection, time.time() - start_db_time
    except mysql.connector.Error as e:
        print(f"Database Connection Error: {e}")
        return None, None

# Convert Decimal values to float for JSON serialization
def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable")

@app.get("/analytics/get_voltage_data")
def get_voltage_data(filter: str):
    total_start_time = time.time()

    try:
        # Establish DB Connection
        mydb, db_time_taken = get_mysql_connection()
        if not mydb:
            return JSONResponse(content={"error": "Database connection failed"}, status_code=500)

        mycursor = mydb.cursor()

        now = datetime.now()
        interval_mapping = {
            "2hr": (now - timedelta(hours=2), 60),
            "1day": (now - timedelta(days=1), 300),
            "1week": (now - timedelta(weeks=1), 900),
            "1month": (now - timedelta(days=30), 3600),
            "3month": (now - timedelta(days=90), 3600),
        }

        if filter not in interval_mapping:
            return JSONResponse(content={"error": "Invalid filter."}, status_code=400)

        start_time, interval = interval_mapping[filter]

        # Query Execution
        query_start_time = time.time()
        query = f"""
        SELECT 
            MIN(deviceTimestamp) AS deviceTimestamp,  
            AVG(R) AS R, 
            AVG(Y) AS Y, 
            AVG(B) AS B,
            AVG(N) AS N
        FROM analytics
        WHERE deviceTimestamp >= %s
         AND parameter = 'Current'
         AND type = 'transformer'
         AND location = 'Substation 15'
         AND bayNumber = 2
        GROUP BY UNIX_TIMESTAMP(deviceTimestamp) DIV {interval}
        ORDER BY deviceTimestamp ASC
        """
        mycursor.execute(query, (start_time,))
        values = mycursor.fetchall()
        query_time_taken = time.time() - query_start_time

        # Data Processing
        processing_start_time = time.time()
        df = pd.DataFrame(values, columns=["deviceTimestamp", "R", "Y", "B", "N"])
        df.dropna(subset=["R", "Y", "B", "N"], inplace=True)

        # Convert Decimal to Float in DataFrame
        df = df.applymap(lambda x: float(x) if isinstance(x, Decimal) else x)

        df["deviceTimestamp"] = df["deviceTimestamp"].astype(str)
        json_data = df.to_dict(orient="records")
        data_processing_time_taken = time.time() - processing_start_time

        mycursor.close()
        mydb.close()

        return JSONResponse(content={
            "data": json_data,
            "timing": {
                "total_time_seconds": time.time() - total_start_time,
                "db_connection_seconds": db_time_taken,
                "query_execution_seconds": query_time_taken,
                "data_processing_seconds": data_processing_time_taken
            }
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7200, reload=True)
>>>>>>> 911b3b1 (Overlays)

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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

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
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345",
            database="alerts",
        )
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.get("/analytics/get_voltage_data")
def get_voltage_data(filter: str):
    try:
        mydb = get_mysql_connection()
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
        else:
            return JSONResponse(content={"error": "Invalid filter."}, status_code=400)

        # Updated query using integer-based binning
        query = f"""
    SELECT 
        MIN(deviceTimestamp) AS deviceTimestamp,  -- Take the first timestamp in each interval
        AVG(R) AS R
    FROM analytics
    WHERE deviceTimestamp >= %s
    GROUP BY UNIX_TIMESTAMP(deviceTimestamp) DIV {interval}
    ORDER BY deviceTimestamp ASC
"""

        mycursor.execute(query, (start_time,))
        values = mycursor.fetchall()

        df = pd.DataFrame(values, columns=["deviceTimestamp", "R"])

        # Ignore null values instead of filling with 0
        df = df.dropna(subset=["R"])
        df["R"] = pd.to_numeric(df["R"], errors="coerce").astype(float)
        df["deviceTimestamp"] = df["deviceTimestamp"].astype(str)

        json_data = df.to_dict(orient="records")

        # Close the cursor and connection
        mycursor.close()
        mydb.close()

        return JSONResponse(content=json_data)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8200, reload=True)

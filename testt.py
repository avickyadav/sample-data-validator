import pyodbc
from sqlalchemy.engine import URL
from sqlalchemy import create_engine, Column, Integer, String, DateTime


server = 'testdbmb.database.windows.net'
database = 'Database1'
username = 'testadmin'
password = 'Ashish@321$'
driver = '{ODBC Driver 18 for SQL Server}'

connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
# connection_string = f"Driver=ODBC Driver 18 for SQL Server;Server=tcp:testdbmb.database.windows.net,1433;Database=Database1;Uid=testadmin;Pwd=Ashish@321+;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
try:
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Persons")
        records = cursor.fetchall()
        for record in records:
            print(record.ID)
            print(record)
except Exception as e:
    print(f"Error: {e}")

# from sqlalchemy.engine import URL
# # connection_string = "DRIVER={SQL Server Native Client 10.0};SERVER=dagger;DATABASE=test;UID=user;PWD=password"
# connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
# print(connection_url)
# engine = create_engine(connection_url)
#
# print(engine)
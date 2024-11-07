import urllib3

from sqlalchemy import create_engine, Column, Integer, String, DateTime, exc
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
server = 'testdbmb.database.windows.net'
database = 'Database1'
username = 'testadmin'
password = 'Ashish@321$'
driver = '{ODBC Driver 18 for SQL Server}'
connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
connect_str = 'mssql+pyodbc:///?odbc_connect=' + urllib3.quote_plus(connection_string)


# Database connection parameters
DATABASE_URL = "mssql+pyodbc://testadmin:Ashish@321$@testdbmb.database.windows.net:1433/Database1?driver=ODBC+Driver+18+for+SQL+Server&encrypt=yes"
# DATABASE_URL = "mssql+pyodbc://?odbc_connect=Driver%3DODBC+Driver+18+for+SQL+Server%3BServer%3Dtcp%3Atestdbmb.database.windows.net%2C1433%3BDatabase%3DDatabase1%3BUid%3Dtestadmin%3BPwd%3DAshish%40321%2B%3BEncrypt%3Dyes%3BTrustServerCertificate%3Dno%3BConnection+Timeout%3D30%3B"
# Set up SQLAlchemy
engine = create_engine(url=DATABASE_URL, pool_pre_ping=True, echo=True)
c = engine.connect()
# a = c.execute('SELECT * FROM Persons')
# print(a)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
# Base = declarative_base()
#
#
# # Define the ORM model for the table
# class Persons(Base):
#     __tablename__ = 'Persons'  # Replace with your actual table name
#     ID = Column(Integer, primary_key=True, index=True)
#     FirstName = Column(String)
#     LastName = Column(String)
#
#
# def retrieve_records():
#     # Create a new session
#     session = SessionLocal()
#     try:
#         # Query to retrieve all records
#         records = session.query(Persons).all()
#
#         # Print the records
#         for record in records:
#             print(record)
#     except Exception as e:
#         print(f"Error: {e}")
#     finally:
#         session.close()
#
#
# if __name__ == "__main__":
#     retrieve_records()

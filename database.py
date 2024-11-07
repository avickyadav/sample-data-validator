from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL

server = 'testdbmb.database.windows.net'
database = 'Database1'
username = 'testadmin'
password = 'Ashish@321$'
driver = '{ODBC Driver 18 for SQL Server}'

connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
print(f'This is url connection {connection_url}')
engine = create_engine(connection_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




class Persons(Base):
    __tablename__ = 'Persons'
    ID = Column(Integer, primary_key=True, index=True)
    FirstName = Column(String)
    LastName = Column(String)


def retrieve_records():
    # Create a new session
    session = SessionLocal()
    try:
        # Query to retrieve all records
        records = session.query(Persons).all()

        # Print the records
        for record in records:
            print(record.ID)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()


retrieve_records()
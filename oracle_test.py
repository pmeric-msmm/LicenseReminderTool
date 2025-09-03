import os
from dotenv import load_dotenv
import oracledb

# Load environment variables
load_dotenv()

def connect_to_oracle():
    """Connect to Oracle database and perform SELECT * from LICENSES table"""
    
    # Get Oracle credentials from environment variables
    oracle_host = os.getenv('ORACLE_HOST')
    oracle_ip = os.getenv('ORACLE_IP')
    oracle_port = int(os.getenv('ORACLE_PORT', 1521))
    oracle_service = os.getenv('ORACLE_SERVICE_NAME')
    oracle_user = os.getenv('ORACLE_USER')
    oracle_password = os.getenv('ORACLE_PASSWORD')
    oracle_schema = os.getenv('ORACLE_SCHEMA')
    oracle_table = os.getenv('ORACLE_TABLE')
    
    # Print connection details (without password)
    print("Oracle Connection Details:")
    print(f"Host: {oracle_host}")
    print(f"IP: {oracle_ip}")
    print(f"Port: {oracle_port}")
    print(f"Service Name: {oracle_service}")
    print(f"User: {oracle_user}")
    print(f"Schema: {oracle_schema}")
    print(f"Table: {oracle_table}")
    print("-" * 50)
    
    # Try both hostname and IP
    for connection_host in [oracle_host, oracle_ip]:
        print(f"\nAttempting connection with: {connection_host}")
        try:
            # Create DSN (Data Source Name)
            dsn = oracledb.makedsn(connection_host, oracle_port, service_name=oracle_service)
            
            # Establish connection
            print("Attempting to connect to Oracle database...")
            connection = oracledb.connect(
                user=oracle_user,
                password=oracle_password,
                dsn=dsn
            )
            
            print("Successfully connected to Oracle database!")
            print("-" * 50)
            
            # Create cursor
            cursor = connection.cursor()
            
            # Execute SELECT query
            query = f"SELECT * FROM {oracle_table}"
            print(f"Executing query: {query}")
            print("-" * 50)
            
            try:
                cursor.execute(query)
                
                # Fetch column names
                columns = [col[0] for col in cursor.description]
                print(f"Columns: {columns}")
                print("-" * 50)
                
                # Fetch all rows
                rows = cursor.fetchall()
                
                print(f"Total rows fetched: {len(rows)}")
                print("-" * 50)
                
                # Display first 5 rows as sample
                if rows:
                    print("Sample data (first 5 rows):")
                    for i, row in enumerate(rows[:5], 1):
                        print(f"\nRow {i}:")
                        for col, val in zip(columns, row):
                            print(f"  {col}: {val}")
                else:
                    print("No data found in the table.")
            except oracledb.Error as query_error:
                print(f"Query execution error: {query_error}")
                # Try with schema prefix
                query = f"SELECT * FROM {oracle_schema}.{oracle_table}"
                print(f"Retrying with schema prefix: {query}")
                cursor.execute(query)
                
                # Fetch column names
                columns = [col[0] for col in cursor.description]
                print(f"Columns: {columns}")
                print("-" * 50)
                
                # Fetch all rows
                rows = cursor.fetchall()
                
                print(f"Total rows fetched: {len(rows)}")
                print("-" * 50)
                
                # Display first 5 rows as sample
                if rows:
                    print("Sample data (first 5 rows):")
                    for i, row in enumerate(rows[:5], 1):
                        print(f"\nRow {i}:")
                        for col, val in zip(columns, row):
                            print(f"  {col}: {val}")
                else:
                    print("No data found in the table.")
            
            # Close cursor and connection
            cursor.close()
            connection.close()
            
            print("\n" + "=" * 50)
            print("Connection closed successfully!")
            
            return True
            
        except oracledb.Error as e:
            print(f"Oracle Database Error with {connection_host}: {e}")
            continue
        except Exception as e:
            print(f"Error with {connection_host}: {e}")
            continue
    
    print("\nFailed to connect using both hostname and IP address.")
    return False

if __name__ == "__main__":
    print("=" * 50)
    print("Oracle Database Connection Test")
    print("=" * 50)
    
    success = connect_to_oracle()
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed! Please check the error messages above.")
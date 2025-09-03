import os
from dotenv import load_dotenv
import oracledb

# Load environment variables
load_dotenv()

def connect_and_query_oracle():
    """Connect to Oracle as SYS/SYSDBA and query LICENSES table"""
    
    # Get credentials from environment
    host = os.getenv('ORACLE_HOST')
    port = int(os.getenv('ORACLE_PORT', 1521))
    service = os.getenv('ORACLE_SERVICE_NAME')
    password = os.getenv('ORACLE_PASSWORD')  # XL4JLLGKCTBD6
    
    # Note: The actual schema name has a space: "MSMM DASHBOARD"
    schema_with_space = "MSMM DASHBOARD"
    table = "LICENSES"
    
    print("=" * 60)
    print("Oracle Database Connection - Working Script")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Service: {service}")
    print(f"Schema: {schema_with_space}")
    print(f"Table: {table}")
    print("=" * 60)
    
    try:
        # Create DSN
        dsn = oracledb.makedsn(host, port, service_name=service)
        
        # Connect as SYS with SYSDBA privilege
        print("\nConnecting to Oracle as SYS/SYSDBA...")
        connection = oracledb.connect(
            user="SYS",
            password=password,
            dsn=dsn,
            mode=oracledb.AUTH_MODE_SYSDBA
        )
        
        print("✓ Successfully connected to Oracle!")
        
        # Create cursor
        cursor = connection.cursor()
        
        # Verify connection
        cursor.execute("SELECT USER FROM DUAL")
        current_user = cursor.fetchone()[0]
        print(f"Connected as: {current_user}")
        print("-" * 60)
        
        # Query LICENSES table with quoted schema name (because of space)
        query = f'SELECT * FROM "{schema_with_space}".{table}'
        print(f"\nExecuting query: {query}")
        print("-" * 60)
        
        cursor.execute(query)
        
        # Get column names
        columns = [col[0] for col in cursor.description]
        print(f"\nColumns ({len(columns)}):")
        for col in columns:
            print(f"  - {col}")
        print("-" * 60)
        
        # Fetch all rows
        rows = cursor.fetchall()
        print(f"\nTotal rows in table: {len(rows)}")
        
        # Display first 5 rows as sample
        if rows:
            print("\nSample data (first 5 rows):")
            print("=" * 60)
            for i, row in enumerate(rows[:5], 1):
                print(f"\nRow {i}:")
                for col, val in zip(columns, row):
                    # Format output based on column name and value type
                    if val is None:
                        print(f"  {col}: NULL")
                    elif isinstance(val, (int, float)):
                        print(f"  {col}: {val}")
                    else:
                        # Truncate long strings for display
                        str_val = str(val)
                        if len(str_val) > 50:
                            print(f"  {col}: {str_val[:50]}...")
                        else:
                            print(f"  {col}: {str_val}")
        else:
            print("\nNo data found in the table.")
        
        # Get count by a specific column if exists (example: by status or type)
        print("\n" + "=" * 60)
        print("Additional Table Statistics:")
        print("-" * 60)
        
        # Count non-null values for each column
        for col in columns[:5]:  # Check first 5 columns
            cursor.execute(f'SELECT COUNT({col}) FROM "{schema_with_space}".{table} WHERE {col} IS NOT NULL')
            count = cursor.fetchone()[0]
            print(f"  {col}: {count} non-null values")
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("✓ Connection test completed successfully!")
        print("✓ Database connection closed.")
        print("=" * 60)
        
        return True
        
    except oracledb.Error as e:
        print(f"\n✗ Oracle Database Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = connect_and_query_oracle()
    
    if success:
        print("\n✅ Script executed successfully!")
        print("You can now use this connection method in your application.")
    else:
        print("\n❌ Script failed. Please check the error messages above.")
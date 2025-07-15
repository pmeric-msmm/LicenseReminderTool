#!/usr/bin/env python3
"""
Generate SQL INSERT statements from Excel data
"""

import pandas as pd
import json
from datetime import datetime

def clean_value_for_sql(value):
    """Clean and format value for SQL insertion"""
    if pd.isna(value) or value is None:
        return 'NULL'
    
    if isinstance(value, str):
        # Escape single quotes and return as string
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return 'NULL'
        return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)
    
    if isinstance(value, datetime):
        return f"'{value.strftime('%Y-%m-%d')}'"
    
    return f"'{str(value)}'"

def generate_sql_inserts():
    """Generate SQL INSERT statements from Excel file"""
    
    # Read Excel file
    df = pd.read_excel('licenses.xlsx')
    
    print("-- SQL INSERT statements for licenses table")
    print("-- Generated on:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    # Create the INSERT statements
    insert_statements = []
    
    for index, row in df.iterrows():
        # Clean and prepare values
        # Skip lic_id since we're using auto-generated id instead
        # lic_id = int(row['LIC_ID']) if not pd.isna(row['LIC_ID']) else None
        lic_name = clean_value_for_sql(row['LIC_NAME'])
        lic_state = clean_value_for_sql(row['LIC_STATE'])
        lic_type = clean_value_for_sql(row['LIC_TYPE'])
        lic_no = clean_value_for_sql(row['LIC_NO'])
        ascem_no = row['ASCEM_NO'] if not pd.isna(row['ASCEM_NO']) else 'NULL'
        
        # Handle dates
        first_issue_date = 'NULL'
        if not pd.isna(row['FIRST_ISSUE_DATE']):
            try:
                date_obj = pd.to_datetime(row['FIRST_ISSUE_DATE'])
                first_issue_date = f"'{date_obj.strftime('%Y-%m-%d')}'"
            except:
                first_issue_date = 'NULL'
        
        expiration_date = 'NULL'
        if not pd.isna(row['EXPIRATION_DATE']):
            try:
                date_obj = pd.to_datetime(row['EXPIRATION_DATE'])
                expiration_date = f"'{date_obj.strftime('%Y-%m-%d')}'"
            except:
                expiration_date = 'NULL'
        
        lic_notify_names = clean_value_for_sql(row['LIC_NOTIFY_NAMES'])
        
        # Create INSERT statement
        sql = f"""INSERT INTO licenses (lic_name, lic_state, lic_type, lic_no, ascem_no, first_issue_date, expiration_date, lic_notify_names)
VALUES ({lic_name}, {lic_state}, {lic_type}, {lic_no}, {ascem_no}, {first_issue_date}, {expiration_date}, {lic_notify_names});"""
        
        insert_statements.append(sql)
    
    # Print all statements
    for statement in insert_statements:
        print(statement)
        print()
    
    print(f"-- Total records: {len(insert_statements)}")
    
    # Also save to file
    with open('license_data_inserts.sql', 'w') as f:
        f.write("-- SQL INSERT statements for licenses table\n")
        f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for statement in insert_statements:
            f.write(statement + '\n\n')
        
        f.write(f"-- Total records: {len(insert_statements)}\n")
    
    print(f"\n✅ SQL statements saved to 'license_data_inserts.sql'")
    print(f"✅ Ready to copy and paste into Supabase SQL editor")

if __name__ == "__main__":
    generate_sql_inserts() 
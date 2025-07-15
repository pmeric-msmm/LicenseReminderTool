#!/usr/bin/env python3
"""
Setup script for License Reminder System
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required Python packages"""
    try:
        print("Installing required dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    env_file = Path(".env")
    template_file = Path("config_template.env")
    
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return True
    
    if template_file.exists():
        try:
            with open(template_file, 'r') as template:
                content = template.read()
            
            with open(env_file, 'w') as env:
                env.write(content)
            
            print("✅ .env file created from template")
            print("⚠️  Please edit .env file with your actual configuration values")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("❌ Template file not found")
        return False

def verify_excel_file():
    """Verify Excel file exists"""
    excel_file = Path("licenses.xlsx")
    if excel_file.exists():
        print("✅ Excel file 'licenses.xlsx' found")
        return True
    else:
        print("⚠️  Excel file 'licenses.xlsx' not found")
        print("   Please ensure your Excel file is named 'licenses.xlsx' or update EXCEL_FILE_PATH in .env")
        return False

def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Edit .env file with your actual configuration:")
    print("   - Supabase URL and API key")
    print("   - Email SMTP settings")
    print("   - Company information")
    
    print("\n2. Set up your Supabase database:")
    print("   - Create a new Supabase project")
    print("   - Run the SQL commands from 'supabase_schema.sql'")
    
    print("\n3. Upload your Excel data:")
    print("   python3 license_reminder_system.py upload")
    
    print("\n4. Test the system:")
    print("   python3 license_reminder_system.py check")
    
    print("\n5. Start the automated scheduler:")
    print("   python3 license_reminder_system.py schedule")
    
    print("\n📧 Email Configuration Tips:")
    print("   - For Gmail: Use App Passwords instead of your regular password")
    print("   - Enable 2-factor authentication and generate an App Password")
    print("   - Other providers: Check their SMTP settings")
    
    print("\n📁 Files created:")
    print("   - .env (configuration file)")
    print("   - supabase_schema.sql (database schema)")
    print("   - license_reminder_system.py (main application)")
    print("   - requirements.txt (Python dependencies)")

def main():
    """Main setup function"""
    print("🚀 License Reminder System Setup")
    print("="*40)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("❌ Setup failed during .env file creation")
        sys.exit(1)
    
    # Verify Excel file
    verify_excel_file()
    
    # Display next steps
    display_next_steps()

if __name__ == "__main__":
    main() 
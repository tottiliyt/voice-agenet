"""
Test script for the collect_time_preferences function tool.
"""
import os
import sys
import logging
import asyncio
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import necessary components
from patient_db import PatientDatabase
from livekit_agent import AssortHealthAgent

# Initialize the database
db = PatientDatabase()

async def test_collect_time_preferences():
    """Test the collect_time_preferences function tool."""
    print("\n=== Testing collect_time_preferences function tool ===\n")
    
    # Create an instance of the agent
    agent = AssortHealthAgent()
    
    # Create a test patient in the database
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # First, check if the test patient already exists
    cursor.execute("SELECT id FROM patients WHERE first_name = 'Test' AND last_name = 'Patient'")
    existing_patient = cursor.fetchone()
    
    if existing_patient:
        patient_id = existing_patient[0]
        print(f"Using existing test patient with ID: {patient_id}")
    else:
        # Insert a test patient
        cursor.execute(
            """
            INSERT INTO patients (
                first_name, last_name, insurance_payer, insurance_id,
                has_referral, referral_physician, medical_complaint,
                street_address, city, state, zip_code, phone_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Test", "Patient", "TestInsurance", "12345",
                0, "", "back pain",
                "123 Test St", "Testville", "CA", "90210", "5551234567"
            )
        )
        conn.commit()
        patient_id = cursor.lastrowid
        print(f"Created new test patient with ID: {patient_id}")
    
    conn.close()
    
    # Set the current_patient_id on the agent
    setattr(agent, 'current_patient_id', patient_id)
    
    # Test time preferences
    time_preferences = "Monday at 3:30 PM"
    print(f"\nTesting with time preferences: {time_preferences}")
    
    # Call the function tool
    result = await agent.collect_time_preferences(time_preferences)
    
    # Print the result
    print("\nRESULT:\n")
    print(result)

# Run the test
if __name__ == "__main__":
    asyncio.run(test_collect_time_preferences())

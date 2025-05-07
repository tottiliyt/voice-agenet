"""
Test script for the select_appointment function in the LiveKit agent.
This script tests the appointment selection and email notification functionality.
"""
import os
import logging
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.agent.livekit_agent import AssortHealthAgent
from src.data.patient_db import PatientDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# Initialize the patient database
db = PatientDatabase()

async def test_select_appointment():
    """Test the select_appointment function."""
    print("\n=== Testing select_appointment function tool ===\n")
    
    # Create a test agent
    agent = AssortHealthAgent()
    
    # Create a test patient if none exists
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Check if we have a test patient
    cursor.execute("SELECT id, first_name, last_name FROM patients LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        patient_id, first_name, last_name = result
        print(f"Using existing test patient with ID: {patient_id}")
    else:
        # Create a test patient
        first_name = "Test"
        last_name = "Patient"
        cursor.execute(
            "INSERT INTO patients (first_name, last_name, medical_complaint) VALUES (?, ?, ?)",
            (first_name, last_name, "back pain")
        )
        conn.commit()
        patient_id = cursor.lastrowid
        print(f"Created new test patient with ID: {patient_id}")
    
    # Set the patient ID in the agent
    agent.current_patient_id = patient_id
    
    # Test the select_appointment function
    doctor = "Dr. Olivia Turner"
    time = "Friday 3:30 PM"
    print(f"Testing with doctor: {doctor} and time: {time}")
    
    result = await agent.select_appointment(doctor, time)
    
    print("\nRESULT:\n")
    print(result)
    
    # Check if the appointment log file was created
    if os.path.exists("appointment_log.txt"):
        print("\nAppointment log file created successfully:")
        with open("appointment_log.txt", "r") as f:
            print(f.read())
    else:
        print("\nWarning: Appointment log file was not created.")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(test_select_appointment())

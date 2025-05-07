"""
Test script for the updated email sending functionality.
"""
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.email_sender import send_appointment_confirmation
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

def test_email():
    print("Testing updated email sending functionality...")
    
    # Test data
    patient_name = "Test Patient"
    doctor_name = "Dr. Jennifer Martinez"
    appointment_time = "Monday, May 12 at 3:30 PM"
    
    # Assort Health team emails
    assort_health_emails = ["jeff@assorthealth.com", "connor@assorthealth.com", "cole@assorthealth.com"]
    print(f"Sending test emails to Assort Health team: {', '.join(assort_health_emails)}")
    
    # Test with HTML injection attempt (should be sanitized)
    patient_name_with_html = "Test Patient <script>alert('XSS')</script>"
    
    print("\nTest 1: Normal email to Assort Health team")
    # Send the test email
    success = send_appointment_confirmation(
        patient_name=patient_name,
        doctor_name=doctor_name,
        appointment_time=appointment_time
    )
    
    if success:
        print(f"✅ Email successfully sent to Assort Health team")
    else:
        print(f"❌ Failed to send email to Assort Health team")
    
    print("\nTest 2: Email with HTML injection attempt (should be sanitized)")
    # Send the test email with HTML injection attempt
    success = send_appointment_confirmation(
        patient_name=patient_name_with_html,
        doctor_name=doctor_name,
        appointment_time=appointment_time
    )
    
    if success:
        print(f"✅ Email with sanitized HTML successfully sent to Assort Health team")
    else:
        print(f"❌ Failed to send email with sanitized HTML to Assort Health team")
    
    print("\nTest 3: Including a patient email")
    # Send the test email with an additional patient email
    patient_email = "patient@example.com"
    success = send_appointment_confirmation(
        patient_name=patient_name,
        doctor_name=doctor_name,
        appointment_time=appointment_time,
        email=patient_email
    )
    
    if success:
        print(f"✅ Email successfully sent to Assort Health team and {patient_email}")
    else:
        print(f"❌ Failed to send email to Assort Health team and {patient_email}")
        
    print("\nTest 4: Invalid additional email address")
    # Send the test email with an invalid additional email
    success = send_appointment_confirmation(
        patient_name=patient_name,
        doctor_name=doctor_name,
        appointment_time=appointment_time,
        email="invalid-email"
    )
    
    if success:
        print("✅ Email successfully sent to Assort Health team (invalid additional email ignored)")
    else:
        print("❌ Failed to send email to Assort Health team")

if __name__ == "__main__":
    test_email()

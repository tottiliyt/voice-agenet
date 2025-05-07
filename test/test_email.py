"""
Test script for the updated email sending functionality.
"""
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from email_sender import send_appointment_confirmation
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
    recipient_email = "tottiliyt@gmail.com"  # Using the same email as in the function default
    
    # Test with HTML injection attempt (should be sanitized)
    patient_name_with_html = "Test Patient <script>alert('XSS')</script>"
    
    print("\nTest 1: Normal email")
    # Send the test email
    success = send_appointment_confirmation(
        patient_name=patient_name,
        doctor_name=doctor_name,
        appointment_time=appointment_time,
        email=recipient_email
    )
    
    if success:
        print(f"✅ Email successfully sent to {recipient_email}")
    else:
        print(f"❌ Failed to send email to {recipient_email}")
    
    print("\nTest 2: Email with HTML injection attempt (should be sanitized)")
    # Send the test email with HTML injection attempt
    success = send_appointment_confirmation(
        patient_name=patient_name_with_html,
        doctor_name=doctor_name,
        appointment_time=appointment_time,
        email=recipient_email
    )
    
    if success:
        print(f"✅ Email with sanitized HTML successfully sent to {recipient_email}")
    else:
        print(f"❌ Failed to send email with sanitized HTML to {recipient_email}")
    
    print("\nTest 3: Invalid email address (should use default)")
    # Send the test email with invalid email
    success = send_appointment_confirmation(
        patient_name=patient_name,
        doctor_name=doctor_name,
        appointment_time=appointment_time,
        email="invalid-email"
    )
    
    if success:
        print("✅ Email successfully sent to default address")
    else:
        print("❌ Failed to send email to default address")

if __name__ == "__main__":
    test_email()

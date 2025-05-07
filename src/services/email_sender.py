"""
Email sender for the Assort Health Voice Agent.
This file contains functions for sending appointment confirmation emails using Gmail.
"""
import os
import yagmail
from dotenv import load_dotenv
from src.utils.logger import logger

# Load environment variables
load_dotenv()

def send_appointment_confirmation(patient_name, doctor_name, appointment_time, email=None):
    """
    Send an appointment confirmation email using Gmail.
    
    Args:
        patient_name: The patient's name
        doctor_name: The selected doctor's name
        appointment_time: The selected appointment time
        email: The email address to send the confirmation to
    
    Returns:
        True if the email was sent successfully, False otherwise
    """
    yag = None
    try:
        # Use Assort Health team emails as recipients
        recipients = ["jeff@assorthealth.com", "connor@assorthealth.com", "cole@assorthealth.com"]
        
        # If a specific email is provided, validate and add it
        if email and '@' in email and '.' in email.split('@')[1]:
            recipients.append(email)
        elif email:
            logger.warning(f"Invalid email address: {email}. Not including in recipients.")
            
        # Get Gmail credentials from environment variables
        gmail_username = os.getenv("GMAIL_USERNAME", "")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")
        
        # If no credentials are provided, log a warning and return
        if not gmail_username or not gmail_password:
            logger.warning("Gmail credentials not found in environment variables. Email not sent.")
            return False
        
        # Sanitize inputs for HTML safety
        safe_patient_name = patient_name.replace('<', '&lt;').replace('>', '&gt;')
        safe_doctor_name = doctor_name.replace('<', '&lt;').replace('>', '&gt;')
        safe_appointment_time = appointment_time.replace('<', '&lt;').replace('>', '&gt;')
        
        # Create the email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #dddddd; border-radius: 5px;">
                <h2 style="color: #0066cc;">Appointment Confirmation</h2>
                <p>Dear {safe_patient_name},</p>
                <p>Your appointment has been scheduled:</p>
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Doctor:</strong> {safe_doctor_name}<br>
                    <strong>Time:</strong> {safe_appointment_time}</p>
                </div>
                <p>If you need to reschedule or have any questions, please call our office.</p>
                <p>Thank you,<br>Assort Health Team</p>
            </div>
        </body>
        </html>
        """
        
        # Initialize Yagmail SMTP
        yag = yagmail.SMTP(gmail_username, gmail_password)
        
        # Send the email to all recipients
        yag.send(
            to=recipients,
            subject=f"Appointment Confirmation for {safe_patient_name}",
            contents=html_content
        )
        
        logger.info(f"Appointment confirmation email sent to {', '.join(recipients)} via Gmail")
        return True
            
    except Exception as e:
        logger.error(f"Error sending appointment confirmation email: {e}")
        return False
    finally:
        # Ensure the SMTP connection is closed
        if yag:
            try:
                yag.close()
            except Exception as close_error:
                logger.warning(f"Error closing SMTP connection: {close_error}")

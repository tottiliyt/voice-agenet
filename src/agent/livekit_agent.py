"""
LiveKit voice agent implementation for the Assort Health Voice Agent.
This file contains the LiveKit agent setup and configuration.
"""
import os
import asyncio
import logging
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.agents.llm import function_tool
from livekit.plugins import (
    openai,
    elevenlabs,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Import from project modules
from src.data.patient_db import PatientDatabase
from src.services.address_validator import validator as address_validator
from src.services.appointment_manager import get_appointment_recommendations
from src.services.email_sender import send_appointment_confirmation
from src.utils.logger import logger

# Load environment variables
load_dotenv()

# Configure logging - set to minimal logging
logging.basicConfig(level=logging.ERROR)  # Only show errors by default

# Configure specific loggers
logging.getLogger("livekit").setLevel(logging.ERROR)  # Only show errors for livekit
logging.getLogger("livekit.agents").setLevel(logging.ERROR)  # Only show errors for livekit.agents
logging.getLogger("httpx").setLevel(logging.ERROR)  # Suppress HTTP request logs
logging.getLogger("httpcore").setLevel(logging.ERROR)  # Suppress HTTP core logs
logging.getLogger("asyncio").setLevel(logging.ERROR)  # Suppress asyncio logs

# Create our application logger
logger = logging.getLogger("livekit_agent")
logger.setLevel(logging.INFO)

# Set patient_db logs to WARNING to reduce initialization messages
logging.getLogger("patient_db").setLevel(logging.WARNING)

# Initialize the patient database (using in-memory SQLite database by default)
db = PatientDatabase()

class AssortHealthAgent(Agent):
    
    def __init__(self):
        # Define the base instructions
        instructions = """
        You are Lois, the Assort Health Voice Agent, a warm, friendly, and caring virtual assistant for medical appointment scheduling. Your tone should be conversational, supportive, and reassuring - like talking to a helpful friend rather than an automated system.
        
        Your job is to collect patient information for scheduling a medical appointment. Follow these steps:
        1. Greet the caller warmly by introducing yourself and asking for their first name and last name. If they only provide first name, gently ask for their last name too.
        2. Confirm the name by warmly repeating it back to them ("Thanks so much! Just to make sure I have it right, your name is [first name] [last name], is that correct?") and wait for confirmation.
        3. After confirmation, collect the patient's name using the collect_patient_name function tool.
        4. Ask for their insurance provider name and policy ID in a friendly, conversational way. 
        5. Confirm the insurance information warmly and read back the policy ID digit by digit ("Great! I've got that you're insured with [provider] and your policy ID is [read each digit: 'one, two, three, four']. Have I got that right?") and wait for confirmation.
        6. After confirmation, collect their insurance information using the collect_insurance_information function tool.
        7. Ask in a friendly way if they have a referral from a physician, and if yes, which physician.
        8. Confirm the referral information conversationally ("Thanks for sharing that. Just to confirm, you [do/don't] have a referral [from Dr. X if applicable]. Is that right?") and wait for confirmation.
        9. After confirmation, collect their referral information using the collect_referral_information function tool.
           - For has_referral, use true if they have a referral, false if not
           - For physician_name, use the physician's name if they have a referral, or an empty string "" if they don't
           - IMPORTANT: Never use null for physician_name, always use an empty string "" if no physician
        10. Ask about their chief medical complaint or reason for the visit in a caring, empathetic way.
        11. Confirm the medical complaint with empathy ("I understand you're coming in for [complaint]. I've got that noted correctly, right?") and wait for confirmation.
        12. After confirmation, collect their medical complaint using the collect_medical_complaint function tool.
        13. Ask for their address information (street address, city, state, and ZIP code) in a friendly, conversational manner. 
        14. Confirm the address warmly and read back the ZIP code digit by digit ("Thank you! So I have your address as [street], [city], [state], and your ZIP code is [read each digit: 'nine, zero, zero, zero, seven']. Is that correct?") and wait for confirmation.
        15. After confirmation, collect their address using the collect_address_information function tool.
           - If the function returns a suggested address, tell the patient: "I found a similar address that might be what you meant. The address I found is [suggested address]. Is this correct?" and wait for their confirmation before proceeding.
           - If they confirm the suggested address, call the collect_address_information function again with the suggested address.
           - If they reject the suggested address, ask them to provide their address again with more details.
           - If the address validation fails completely, gently inform the patient and ask them to verify their address
        16. Ask for their phone number in a friendly way. 
        17. Confirm the phone number by reading back each digit individually ("Perfect! I have your phone number as [read each digit: 'five, five, five, one, two, three, four, five, six, seven']. Did I get that right?") and wait for confirmation. 
        18. After confirmation, collect their phone number using the collect_phone_number function tool.
        19. Ask if they would like to provide an email address (make it clear this is optional) in a warm, no-pressure way.
        20. If they want to provide an email, confirm by spelling it out character by character ("Wonderful! I have your email as [spell out each character: 'j-o-h-n-dot-d-o-e-at-g-m-a-i-l-dot-c-o-m']. Is that spelled correctly?") and wait for confirmation.
        21. After confirmation, collect it using the collect_email function tool.
        22. Ask about their preferred appointment day and time in a friendly way ("Now, let's find a good time for your appointment. What day and time would work best for you?").
        23. Confirm their time preferences ("So you prefer [time preferences]. Is that correct?") and wait for confirmation.
        24. When the patient shares their time preferences, format it consistently as either "[Day of week] at [time]" (e.g., "Monday at 3:30 PM") or "[Month] [day] at [time]" (e.g., "May 25 at 3:30 PM") before passing it to the function tool.
        25. After confirmation, collect their time preferences using the collect_time_preferences function tool.
        26. The system will provide appointment recommendations based on their medical concern and time preferences.
        27. Ask which option they prefer ("Which of these options would work best for you? You can say the number or the doctor's name and time.").
        28. If they ask for more options, politely apologize and explain that these are the best matches for their needs, then repeat the top 3 options.
        29. When they select an option, confirm their selection ("Great! Just to confirm, you'd like to see [doctor] on [day] at [time]. Is that correct?") and wait for confirmation.
        30. After confirmation, record their selection using the select_appointment function tool.
        31. Thank them warmly for scheduling, confirm their appointment details, and let them know they'll receive a confirmation.
        32. After confirming the appointment, don't end the call immediately. Instead, engage in a brief, friendly conversation:
            - Ask if they have any questions about their upcoming appointment
            - Only end the call after this friendly wrap-up conversation
        
        Guidelines:
        - Be warm, friendly, and conversational throughout the call - use a natural, caring tone
        - Use the caller's name occasionally to personalize the conversation
        - Express empathy and understanding, especially when discussing medical concerns
        - Use friendly acknowledgments like "Great!", "Perfect!", "Thank you so much!"
        - Speak clearly at a comfortable, unhurried pace
        - When confirming, repeat back information in a natural, friendly way
        - If the patient corrects information, respond with appreciation ("Thanks for the correction!") 
        - Reassure the patient when they provide information ("That's exactly what I needed")
        - Use the provided function tools to collect and store patient information
        - Pay attention to the return values from function tools to guide your responses
        - End the call with genuine warmth and appreciation

        """
        
        super().__init__(instructions=instructions)
    
    async def on_enter(self):
        """Called when the agent enters the conversation."""
        # Generate the initial greeting
        await self.session.generate_reply()
    
    @function_tool
    async def collect_patient_name(self, first_name: str, last_name: str):
        """
        Collect the patient's name.
        
        Args:
            first_name: The patient's first name
            last_name: The patient's last name
        """
        # Store the patient's name in the database
        full_name = f"{first_name} {last_name}"
        
        # Create a new patient record in the database
        patient_id = db.create_patient(first_name, last_name)
        
        # Store the patient ID in the agent instance for later use
        self.current_patient_id = patient_id
        
        logger.info(f"Collected patient name: {full_name} (ID: {patient_id})")
        return f"Thank you, {first_name}. I've recorded your name. Now, could you please provide your insurance information? I'll need both your insurance provider name and your policy ID number."
    
    @function_tool
    async def collect_insurance_information(self, provider: str, policy_id: str):
        """
        Collect the patient's insurance information.
        
        Args:
            provider: The insurance provider/payer name
            policy_id: The insurance policy ID
        """
        try:
            # Get the current patient ID
            patient_id = getattr(self, 'current_patient_id', None)
            
            if not patient_id:
                logger.error("No current patient ID found when collecting insurance information")
                return "I'm sorry, but I need to collect your name first before recording your insurance details. Could you please tell me your full name?"
            
            # Update the insurance information in the database
            success = db.update_insurance(patient_id, provider, policy_id)
            
            if not success:
                logger.error(f"Failed to update insurance for patient ID: {patient_id}")
                return "I'm sorry, but there was an error processing your insurance information. Could you please provide it again?"
            
            logger.info(f"Collected insurance information for patient ID {patient_id}: {provider}, {policy_id}")
            return f"Thank you for providing your insurance information. I've recorded that you have {provider} with policy ID {policy_id}. Now, do you have a referral from a physician for this appointment?"
        
        except Exception as e:
            logger.error(f"Error collecting insurance information: {e}")
            return "I'm sorry, but there was an error processing your insurance information. Could you please provide it again?"
    
    @function_tool
    async def collect_referral_information(self, has_referral: bool, physician_name: str = ""):
        """
        Collect the patient's referral information.
        
        Args:
            has_referral: Whether the patient has a referral
            physician_name: The name of the referring physician (if has_referral is True, otherwise empty string)
        """
        try:
            # Get the current patient ID
            patient_id = getattr(self, 'current_patient_id', None)
            
            if not patient_id:
                logger.error("No current patient ID found when collecting referral information")
                return "I'm sorry, but I need to collect your basic information first before recording your referral details. Could you please tell me your full name?"
            
            # Update the referral information in the database
            success = db.update_referral(patient_id, has_referral, physician_name)
            
            if not success:
                logger.error(f"Failed to update referral for patient ID: {patient_id}")
                return "I'm sorry, but there was an error processing your referral information. Could you please provide it again?"
            
            logger.info(f"Collected referral information for patient ID {patient_id}: has_referral={has_referral}, physician={physician_name}")
            
            if has_referral and physician_name:
                return f"Thank you. I've recorded that you have a referral from Dr. {physician_name}. Now, could you please tell me the reason for your visit or your chief medical complaint?"
            else:
                return "Thank you. I've noted that you don't have a referral. Now, could you please tell me the reason for your visit or your chief medical complaint?"
        
        except Exception as e:
            logger.error(f"Error collecting referral information: {e}")
            return "I'm sorry, but there was an error processing your referral information. Could you please provide it again?"
    
    @function_tool
    async def collect_medical_complaint(self, complaint: str):
        """
        Collect the patient's chief medical complaint or reason for visit.
        
        Args:
            complaint: The patient's medical complaint or reason for visit
        """
        try:
            # Get the current patient ID
            patient_id = getattr(self, 'current_patient_id', None)
            
            if not patient_id:
                logger.error("No current patient ID found when collecting medical complaint")
                return "I'm sorry, but I need to collect your basic information first before recording your reason for visit. Could you please tell me your full name?"
            
            # Update the medical complaint in the database
            success = db.update_medical_complaint(patient_id, complaint)
            
            if not success:
                logger.error(f"Failed to update medical complaint for patient ID: {patient_id}")
                return "I'm sorry, but there was an error processing your reason for visit. Could you please provide it again?"
            
            logger.info(f"Collected medical complaint for patient ID {patient_id}: {complaint}")
            return f"Thank you for sharing your reason for visit. I've recorded that you're seeking an appointment for: {complaint}. Now, I need to collect your address information. Could you please provide your street address, city, state, and ZIP code?"
        
        except Exception as e:
            logger.error(f"Error collecting medical complaint: {e}")
            return "I'm sorry, but there was an error processing your reason for visit. Could you please provide it again?"
    
    @function_tool
    async def collect_address_information(self, street_address: str, city: str, state: str, zip_code: str):
        """
        Collect and validate the patient's address information.
        
        Args:
            street_address: The street address (e.g., "123 Main St")
            city: The city name
            state: The state abbreviation (e.g., "CA")
            zip_code: The ZIP code
        """
        try:
            # Get the current patient ID
            patient_id = getattr(self, 'current_patient_id', None)
            
            if not patient_id:
                logger.error("No current patient ID found when collecting address information")
                return "I'm sorry, but I need to collect your basic information first before recording your address. Could you please tell me your full name?"
            
            # Validate the address using SmartyStreets API
            is_valid, formatted_address, is_suggestion = address_validator.validate_address(
                street_address, city, state, zip_code
            )
            
            # If the address is valid (either exact or suggested match), use the standardized format
            if is_valid and formatted_address:
                street = formatted_address["street_address"]
                city = formatted_address["city"]
                state = formatted_address["state"]
                zip_code = formatted_address["zip_code"]
                
                # If this is a suggested address (not an exact match), ask for confirmation
                if is_suggestion:
                    # Don't save yet, just return the suggested address for confirmation
                    logger.info(f"Found suggested address match: {street}, {city}, {state} {zip_code}")
                    return f"I found a similar address that might be what you meant: {street}, {city}, {state} {zip_code}. Is this correct? If yes, please say 'yes' and I'll save it. If not, please provide your address again."
                
                # For exact matches or after confirmation, save the address
                # Update the address in the database
                success = db.update_address(
                    patient_id, street, city, state, zip_code
                )
                
                if not success:
                    logger.error(f"Failed to update address for patient ID: {patient_id}")
                    return "I'm sorry, but there was an error saving your address. Could you please provide it again?"
                
                logger.info(f"Collected validated address for patient ID {patient_id}: {street}, {city}, {state} {zip_code}")
                return f"Thank you. I've recorded your address as {street}, {city}, {state} {zip_code}. Now, I need your contact information. Could you please provide your phone number, and optionally your email address?"
            
            # If the address validation failed (no match found)
            else:
                # Don't save invalid addresses
                logger.warning(f"No address matches found for: {street_address}, {city}, {state} {zip_code}")
                
                # If we have SmartyStreets credentials but validation failed
                if address_validator.client:
                    return f"I couldn't find a match for the address you provided: {street_address}, {city}, {state} {zip_code}. Please check the address and try again. Make sure to include the street number, name, and correct ZIP code."
                # If SmartyStreets is not configured
                else:
                    return f"I'm unable to validate addresses at this time. Please verify that you provided: {street_address}, {city}, {state} {zip_code}. If this is correct, please say 'yes' and we'll continue with your phone number."
        
        except Exception as e:
            logger.error(f"Error collecting address information: {e}")
            return "I'm sorry, but there was an error processing your address information. Could you please provide it again?"
    
    @function_tool
    async def collect_phone_number(self, phone_number: str):
        """
        Collect the patient's phone number.
        
        Args:
            phone_number: The patient's phone number
        """
        try:
            # Get the current patient ID
            patient_id = getattr(self, 'current_patient_id', None)
            
            if not patient_id:
                logger.error("No current patient ID found when collecting phone number")
                return "I'm sorry, but I need to collect your basic information first before recording your phone number. Could you please tell me your full name?"
            
            # Basic validation for phone number format
            # Remove any non-digit characters
            clean_phone = re.sub(r'\D', '', phone_number)
            
            # Check if we have a valid US phone number (10 digits)
            if len(clean_phone) != 10:
                return f"The phone number you provided doesn't appear to be a valid 10-digit US phone number. Please provide a valid phone number in the format XXX-XXX-XXXX."
            
            # Format the phone number nicely
            formatted_phone = f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}"
            
            # Update the phone number in the database
            success = db.update_phone_number(patient_id, formatted_phone)
            
            if not success:
                logger.error(f"Failed to update phone number for patient ID: {patient_id}")
                return "I'm sorry, but there was an error saving your phone number. Could you please provide it again?"
            
            logger.info(f"Collected phone number for patient ID {patient_id}: {formatted_phone}")
            
            return f"Thank you for providing your phone number. I've recorded it as {formatted_phone}. Would you also like to provide an email address? This is optional, but it gives us another way to contact you about your appointment."
        
        except Exception as e:
            logger.error(f"Error collecting phone number: {e}")
            return "I'm sorry, but there was an error processing your phone number. Could you please provide it again?"
    
    @function_tool
    async def collect_email(self, email: str):
        """
        Collect the patient's email address (optional).
        
        Args:
            email: The patient's email address
        """
        try:
            # Get the current patient ID
            patient_id = getattr(self, 'current_patient_id', None)
            
            if not patient_id:
                logger.error("No current patient ID found when collecting email")
                return "I'm sorry, but I need to collect your basic information first before recording your email. Could you please tell me your full name?"
            
            # Handle case where user doesn't want to provide email
            if email.lower() in ["no", "none", "no email", "skip", "no thanks", "pass"]:
                logger.info(f"User declined to provide email for patient ID {patient_id}")
                return "That's perfectly fine. Now, let's find a good time for your appointment. What days and times work best for you?"
            
            # Basic validation for email
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$', email):
                return f"The email address you provided doesn't appear to be valid. Please provide a valid email address or say 'no' if you prefer not to provide one."
            
            # Update the email in the database
            success = db.update_email(patient_id, email)
            
            if not success:
                logger.error(f"Failed to update email for patient ID: {patient_id}")
                return "I'm sorry, but there was an error saving your email address. Could you please provide it again?"
            
            logger.info(f"Collected email for patient ID {patient_id}: {email}")
            
            return f"Thank you for providing your email address. I've recorded it as {email}. Now, let's find a good time for your appointment. What days and times work best for you?"
        
        except Exception as e:
            logger.error(f"Error collecting email: {e}")
            return "I'm sorry, but there was an error processing your email address. Could you please provide it again?"
            
    @function_tool
    async def collect_time_preferences(self, time_preferences: str) -> str:
        """
        Collect the patient's time preferences and provide appointment recommendations.
        
        Args:
            time_preferences: The patient's preferred days/times for the appointment
            
        Returns:
            A formatted string with the top 3 recommended doctors and times
        """
        try:
            # Log the time preferences
            logging.info(f"Collecting time preferences: {time_preferences}")
            
            # Get the patient ID
            patient_id = getattr(self, 'current_patient_id', None)
            if not patient_id:
                logging.error("No patient ID found")
                return "I'm sorry, but I'm having trouble accessing your information. Let me connect you with our scheduling team."
            
            # Connect to the database
            try:
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()
                
                # Get the patient's medical complaint
                cursor.execute("SELECT medical_complaint FROM patients WHERE id = ?", (patient_id,))
                result = cursor.fetchone()
                
                if not result:
                    logging.error(f"No patient found with ID {patient_id}")
                    return "I'm sorry, but I'm having trouble accessing your information. Let me connect you with our scheduling team."
                
                medical_complaint = result[0]
                logging.info(f"Retrieved medical complaint for patient {patient_id}: {medical_complaint}")
                
            except sqlite3.Error as e:
                logging.error(f"Database error: {e}")
                return "I'm sorry, but I'm having trouble accessing your information. Let me connect you with our scheduling team."
            finally:
                conn.close()
            
            # Get appointment recommendations
            logging.info(f"Getting appointment recommendations for medical concern: {medical_complaint}, time preferences: {time_preferences}")
            recommendations = get_appointment_recommendations(medical_complaint, time_preferences)
            logging.info(f"Received recommendations: {recommendations[:100]}...")
            
            return recommendations
            
        except Exception as e:
            logging.error(f"Error in collect_time_preferences: {e}")
            return "I'm sorry, but I'm having trouble finding appointment options for you. Our scheduling team will contact you to arrange an appointment that meets your needs."
            
    @function_tool
    async def select_appointment(self, doctor: str, time: str) -> str:
        """
        Record the patient's selected appointment and send a confirmation email.
        
        Args:
            doctor: The selected doctor's name
            time: The selected appointment time
            
        Returns:
            A confirmation message
        """
        try:
            # Log the selection
            logging.info(f"Selecting appointment with {doctor} at {time}")
            
            # Get the patient ID
            patient_id = getattr(self, 'current_patient_id', None)
            if not patient_id:
                logging.error("No patient ID found")
                return "I'm sorry, but I'm having trouble accessing your information. Let me connect you with our scheduling team."
            
            # Variables to store patient info
            patient_name = "Patient"
            medical_complaint = "medical concern"
            
            # Connect to the database
            conn = None
            try:
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()
                
                # Get the patient's information
                cursor.execute("SELECT first_name, last_name, medical_complaint FROM patients WHERE id = ?", (patient_id,))
                result = cursor.fetchone()
                
                if result:
                    first_name, last_name, medical_complaint = result
                    patient_name = f"{first_name} {last_name}"
                    
                    # Update the patient record with appointment details
                    cursor.execute(
                        "UPDATE patients SET appointment_doctor = ?, appointment_time = ? WHERE id = ?",
                        (doctor, time, patient_id)
                    )
                    conn.commit()
                
            except sqlite3.Error as e:
                logging.error(f"Database error in select_appointment: {e}")
                # Continue with the function even if database operations fail
            finally:
                if conn:
                    conn.close()
            
            # Try to send confirmation email, but don't let failures stop the function
            email_sent = False
            try:
                email_sent = send_appointment_confirmation(patient_name, doctor, time)
            except Exception as email_error:
                logging.error(f"Email error in select_appointment: {email_error}")
            
            # Return success message regardless of email status
            if email_sent:
                return f"Great! I've scheduled your appointment with {doctor} on {time} for your {medical_complaint}. A confirmation email has been sent with these details. Our scheduling team may contact you if any additional information is needed. Thank you for choosing Assort Health!"
            else:
                return f"Great! I've scheduled your appointment with {doctor} on {time} for your {medical_complaint}. Our scheduling team will contact you shortly to confirm these details. Thank you for choosing Assort Health!"
            
        except Exception as e:
            logging.error(f"Error in select_appointment: {e}")
            return "I've noted your appointment selection. Our team will contact you shortly to finalize the details. Thank you for your patience."
    
    

async def entrypoint(ctx: agents.JobContext):
    """
    Entry point for the LiveKit agent.
    This function is called when a new call is received.
    
    Args:
        ctx: The JobContext containing information about the call
    """
    # Get the room name from the context
    room_name = ctx.room.name if ctx.room else "unknown"
    
    # Log the start of the agent session
    logger.info(f"Starting LiveKit agent session for room {room_name}")
    
    # Connect to the room
    await ctx.connect()
    
    # Create an agent session with the necessary components
    
    # Create the agent session with improved STT configuration
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="en"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=elevenlabs.TTS(),  # Using ElevenLabs for TTS
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )
    
    try:
        # Start the agent session
        logger.info(f"Starting agent session for room {room_name}")
        await session.start(
            room=ctx.room,
            agent=AssortHealthAgent(),
            room_input_options=RoomInputOptions(
                # LiveKit Cloud enhanced noise cancellation
                # For telephony applications, use BVC for best results
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )
        
        # The on_enter method of our agent will handle the initial greeting
        # No need to call generate_reply here as it's handled in the agent
        
        # Log that we're waiting for user input
        logger.info(f"Waiting for user input in room {room_name}")
        
        # Main conversation loop is handled automatically by LiveKit
        
    except Exception as e:
        # Log any errors that occur during the session
        logger.error(f"Error in agent session for room {room_name}: {e}")

async def create_and_join_room(call_sid):
    """
    Create and join a LiveKit room for a Twilio call.
    
    Args:
        call_sid: The Twilio call SID
        
    Returns:
        The LiveKit room name
    """
    # Generate a unique room name based on the call SID
    room_name = f"assort-health-call_{call_sid}"
    
    # Return the room name
    return room_name

if __name__ == "__main__":
    # Run the agent as a standalone application
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

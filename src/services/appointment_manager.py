"""
Appointment manager for the Assort Health Voice Agent.
This file contains functions for AI-based doctor-patient matching.
"""
import os
import json
import re
import random
import logging
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import openai
from src.utils.logger import logger

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger("appointment_manager")

# Load doctor data from JSON file
def load_doctors_data():
    """
    Load doctor data from the JSON file.
    If the file is not found or has errors, return a minimal default dataset.
    """
    try:
        import os
        # Get the path to the src directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        json_path = os.path.join(src_dir, 'data', 'doctors_data.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as file:
                data = json.load(file)
                return data
        else:
            logger.error(f"Doctor data file not found at: {json_path}")
            return {"doctors": []}
    except Exception as e:
        logger.error(f"Error loading doctor data: {e}")
        # Return minimal default data
        return {"doctors": []}

# Load the doctors data
DOCTORS = load_doctors_data()

def get_appointment_recommendations(medical_concern, time_preferences):
    """
    Use AI to recommend the best doctor and appointment times based on
    the patient's medical concern and time preferences.
    
    Args:
        medical_concern: The patient's medical complaint or reason for visit
        time_preferences: The patient's preferred days/times for the appointment
        
    Returns:
        A formatted string with the top 3 recommended doctors and times
    """
    try:
        # Ensure we have the OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found in environment variables")
            return "I'm sorry, but I'm having trouble accessing our scheduling system. Our team will contact you to arrange an appointment."
        
        # Get the current date for context
        current_date = datetime.now()
        
        # Extract requested time if present
        requested_time = None
        time_pattern = r'(\d{1,2})(?::(\d{2}))? ?(AM|PM)'
        time_match = re.search(time_pattern, time_preferences, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            am_pm = time_match.group(3).upper()
            if am_pm == 'PM' and hour < 12:
                hour += 12
            elif am_pm == 'AM' and hour == 12:
                hour = 0
            requested_time = f"{hour:02d}:{minute:02d}"
            logger.info(f"Extracted requested time: {requested_time}")
        
        # Parse date and determine day of week
        requested_day = None
        requested_date = None
        
        # Try to extract a specific date (e.g., "May 25")
        month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})'
        date_match = re.search(month_pattern, time_preferences)
        
        if date_match:
            month_name = date_match.group(1)
            day = int(date_match.group(2))
            
            # Convert month name to number
            month_names = ["January", "February", "March", "April", "May", "June", 
                          "July", "August", "September", "October", "November", "December"]
            month_num = month_names.index(month_name) + 1
            
            # Create a date object for 2025
            requested_date = date(2025, month_num, day)
            requested_day = requested_date.strftime('%A')
            logger.info(f"Determined that {time_preferences} falls on a {requested_day}")
        else:
            # Try to extract day of week directly (e.g., "Monday")
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for day in days:
                if day.lower() in time_preferences.lower():
                    requested_day = day
                    # Calculate the next occurrence of this day
                    today = current_date.date()
                    today_idx = today.weekday()  # 0 = Monday, 6 = Sunday
                    day_idx = days.index(day)
                    days_until = (day_idx - today_idx) % 7
                    if days_until == 0:  # Same day, so use next week
                        days_until = 7
                    requested_date = today + timedelta(days=days_until)
                    logger.info(f"Found day of week {day} in request, next occurrence is {requested_date}")
                    break
        
        # If we couldn't determine a day, default to the next business day
        if not requested_day:
            logger.info(f"Could not determine specific day from '{time_preferences}', defaulting to next business day")
            today = current_date.date()
            days_to_add = 1
            if today.weekday() >= 4:  # Friday (4) or weekend
                days_to_add = 7 - today.weekday()
            requested_date = today + timedelta(days=days_to_add)
            requested_day = requested_date.strftime('%A')
        
        # Find doctors available on the requested day
        available_doctors = []
        for doctor in DOCTORS["doctors"]:
            for time_slot in doctor["available_times"]:
                if time_slot.startswith(requested_day):
                    available_doctors.append(doctor)
                    break
        
        # If no doctors available on requested day, find closest available day
        if not available_doctors:
            logger.info(f"No doctors available on {requested_day}, finding closest available day")
            day_indices = {day: idx for idx, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])}
            requested_idx = day_indices[requested_day]
            
            # Check days in order of proximity to requested day
            for offset in range(1, 7):
                for direction in [1, -1]:  # Try both forward and backward
                    check_idx = (requested_idx + direction * offset) % 7
                    check_day = list(day_indices.keys())[check_idx]
                    
                    # Find doctors available on this day
                    for doctor in DOCTORS["doctors"]:
                        for time_slot in doctor["available_times"]:
                            if time_slot.startswith(check_day):
                                if doctor not in available_doctors:
                                    available_doctors.append(doctor)
                    
                    if available_doctors:
                        # Calculate the actual date for this day
                        days_diff = (check_idx - requested_idx) % 7
                        if days_diff > 3:  # If it's more than 3 days forward, it's actually backward
                            days_diff = days_diff - 7
                        adjusted_date = requested_date + timedelta(days=days_diff)
                        requested_day = check_day
                        requested_date = adjusted_date
                        logger.info(f"Found doctors available on {check_day}, {adjusted_date}")
                        break
                
                if available_doctors:
                    break
        
        # Create a filtered list of doctors for the AI to choose from
        filtered_doctors = {"doctors": available_doctors}
        
        # Format the date string for the AI
        date_str = requested_date.strftime("%B %d")
        formatted_day_date = f"{requested_day}, {date_str}"
        
        # Create the prompt for the AI
        prompt = f"""You are a medical appointment scheduler. Your task is to match a patient with the most appropriate doctor based on their medical concern.

Patient's medical concern: {medical_concern}

I've already filtered the doctors to only show those available on {formatted_day_date}. Please recommend the top 3 most appropriate doctors for this patient's medical concern.

Available doctors and their specialties:
{json.dumps(filtered_doctors, indent=2)}

Please recommend the top 3 most appropriate doctors for this patient. Consider:
1. The doctor's specialty and expertise in relation to the patient's medical concern
2. The urgency of the medical concern
3. DIVERSITY - recommend different doctors with different specialties if possible

Format your response as a JSON object with the following structure:
{{
  "recommendations": [
    {{"doctor": "Doctor's full name", "time": "{formatted_day_date} at 3:30 PM"}},
    {{"doctor": "Doctor's full name", "time": "{formatted_day_date} at 2:00 PM"}},
    {{"doctor": "Doctor's full name", "time": "{formatted_day_date} at 10:30 AM"}}
  ]
}}
"""
        
        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using the same model as the agent
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Format the recommendations for the patient
        formatted_response = "Based on your medical concern and time preferences, here are the best appointment options I can offer:\n\n"
        
        for i, rec in enumerate(result["recommendations"], 1):
            formatted_response += f"{i}. {rec['doctor']} - {rec['time']}\n\n"
        
        formatted_response += "Which of these options would you prefer? You can say the number (1, 2, or 3) or the doctor's name and time."
        
        logger.info(f"Successfully formatted response with {len(result['recommendations'])} recommendations")
        return formatted_response
        
    except Exception as e:
        logger.error(f"Error getting appointment recommendations: {e}")
        return "I'm sorry, but I'm having trouble finding the best appointment options for you. Our scheduling team will contact you to arrange an appointment that meets your needs."



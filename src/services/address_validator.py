"""
Address validation module for the Assort Health Voice Agent.
Uses SmartyStreets API to validate US addresses.
"""
import os
import logging
from dotenv import load_dotenv
from smartystreets_python_sdk import ClientBuilder, StaticCredentials, exceptions
from smartystreets_python_sdk.us_street import Lookup as StreetLookup
from src.utils.logger import logger
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# SmartyStreets API credentials
SMARTY_AUTH_ID = os.getenv("SMARTY_AUTH_ID")
SMARTY_AUTH_TOKEN = os.getenv("SMARTY_AUTH_TOKEN")

class AddressValidator:
    """Address validation using SmartyStreets API."""
    
    def __init__(self):
        """Initialize the address validator with SmartyStreets credentials."""
        if not all([SMARTY_AUTH_ID, SMARTY_AUTH_TOKEN]):
            logger.warning("SmartyStreets credentials not found. Address validation will be disabled.")
            self.client = None
        else:
            # Create a credentials object with your SmartyStreets auth ID and auth token
            credentials = StaticCredentials(SMARTY_AUTH_ID, SMARTY_AUTH_TOKEN)
            
            # Create a client object for the US Street API using ClientBuilder
            client_builder = ClientBuilder(credentials)
            self.client = client_builder.build_us_street_api_client()
            
            logger.info("Address validator initialized with SmartyStreets API")
    
    def validate_address(self, street_address: str, city: str, state: str, zip_code: str):
        """
        Validate a US address using SmartyStreets API.
        
        Args:
            street_address: The street address (e.g., "123 Main St")
            city: The city name
            state: The state abbreviation (e.g., "CA")
            zip_code: The ZIP code
            
        Returns:
            A tuple containing (is_valid, formatted_address, is_suggestion)
            - is_valid: Boolean indicating if the address is valid
            - formatted_address: Dictionary with standardized address components if valid
            - is_suggestion: Boolean indicating if this is a suggested match rather than exact
        """
        if not self.client:
            logger.warning("Address validation attempted but SmartyStreets credentials not configured")
            return False, None, False
        
        # First try with strict matching
        lookup = StreetLookup()
        lookup.street = street_address
        lookup.city = city
        lookup.state = state
        lookup.zipcode = zip_code
        lookup.match = "strict"  # First try with strict match
        
        try:
            # Send the lookup to the API
            self.client.send_lookup(lookup)
            
            # Check if we got a valid match with strict matching
            if lookup.result:
                result = lookup.result[0]
                
                # Extract the standardized address components
                formatted_address = {
                    "street_address": f"{result.components.primary_number} {result.components.street_name} {result.components.street_suffix}",
                    "city": result.components.city_name,
                    "state": result.components.state_abbreviation,
                    "zip_code": result.components.zipcode,
                    "plus4_code": result.components.plus4_code
                }
                
                logger.info(f"Address validated successfully with strict match: {formatted_address}")
                return True, formatted_address, False  # Not a suggestion
            
            # If no strict match, try with enhanced matching (looser)
            lookup = StreetLookup()
            lookup.street = street_address
            lookup.city = city
            lookup.state = state
            lookup.zipcode = zip_code
            lookup.match = "enhanced"  # Try with enhanced (looser) matching
            
            self.client.send_lookup(lookup)
            
            if lookup.result:
                result = lookup.result[0]
                
                # Extract the standardized address components
                formatted_address = {
                    "street_address": f"{result.components.primary_number} {result.components.street_name} {result.components.street_suffix}",
                    "city": result.components.city_name,
                    "state": result.components.state_abbreviation,
                    "zip_code": result.components.zipcode,
                    "plus4_code": result.components.plus4_code
                }
                
                logger.info(f"Found similar address match: {formatted_address}")
                return True, formatted_address, True  # This is a suggestion
            
            logger.warning(f"No address matches found for: {street_address}, {city}, {state} {zip_code}")
            return False, None, False
                
        except exceptions.SmartyException as err:
            logger.error(f"Error validating address: {err}")
            return False, None, False

# Create a singleton instance
validator = AddressValidator()

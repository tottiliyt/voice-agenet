import os
import sqlite3
import logging
from pathlib import Path
from src.utils.logger import logger

class PatientDatabase:
    def __init__(self, db_path: str = None, recreate: bool = False):
        """
        Initialize the patient database.
        
        Args:
            db_path: Path to the database file. If None, uses default path.
            recreate: If True, recreates the database from scratch.
        """
        if db_path is None:
            # Use a default path in the same directory as this file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'patient_data.db')
        
        self.db_path = db_path
        
        # If recreate is True, delete the existing database file
        if recreate and os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
                logger.info(f"Deleted existing database at {self.db_path}")
            except Exception as e:
                logger.error(f"Error deleting database: {e}")
        
        self._initialize_db()
    
    def _initialize_db(self):
        """Create the database and tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create patients table with name, insurance, referral, medical complaint, address, contact information, and appointment details
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            insurance_payer TEXT,
            insurance_id TEXT,
            has_referral BOOLEAN,
            referral_physician TEXT,
            medical_complaint TEXT,
            street_address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            phone_number TEXT,
            email TEXT,
            appointment_doctor TEXT,
            appointment_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Patient database initialized at {self.db_path}")
    
    def create_patient(self, first_name: str, last_name: str) -> int:
        """Create a new patient record. Returns patient ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create new patient
        cursor.execute(
            "INSERT INTO patients (first_name, last_name) VALUES (?, ?)",
            (first_name, last_name)
        )
        patient_id = cursor.lastrowid
        logger.info(f"Created new patient: {first_name} {last_name} (ID: {patient_id})")
        
        conn.commit()
        conn.close()
        return patient_id
        
    def update_insurance(self, patient_id: int, payer_name: str, policy_id: str) -> bool:
        """Update a patient's insurance information. Returns success status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update insurance information
            cursor.execute(
                "UPDATE patients SET insurance_payer = ?, insurance_id = ? WHERE id = ?",
                (payer_name, policy_id, patient_id)
            )
            
            if cursor.rowcount == 0:
                logger.error(f"No patient found with ID: {patient_id}")
                conn.close()
                return False
                
            logger.info(f"Updated insurance for patient ID {patient_id}: {payer_name}, {policy_id}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating insurance: {e}")
            conn.close()
            return False
            
    def update_referral(self, patient_id: int, has_referral: bool, physician: str = "") -> bool:
        """Update a patient's referral information. Returns success status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # If has_referral is False, ensure physician is empty
            if not has_referral:
                physician = ""
                
            # Update referral information
            cursor.execute(
                "UPDATE patients SET has_referral = ?, referral_physician = ? WHERE id = ?",
                (has_referral, physician, patient_id)
            )
            
            if cursor.rowcount == 0:
                logger.error(f"No patient found with ID: {patient_id}")
                conn.close()
                return False
                
            logger.info(f"Updated referral for patient ID {patient_id}: has_referral={has_referral}, physician={physician}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating referral: {e}")
            conn.close()
            return False
            
    def update_medical_complaint(self, patient_id: int, complaint: str) -> bool:
        """Update a patient's medical complaint. Returns success status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update medical complaint
            cursor.execute(
                "UPDATE patients SET medical_complaint = ? WHERE id = ?",
                (complaint, patient_id)
            )
            
            if cursor.rowcount == 0:
                logger.error(f"No patient found with ID: {patient_id}")
                conn.close()
                return False
                
            logger.info(f"Updated medical complaint for patient ID {patient_id}: {complaint}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating medical complaint: {e}")
            conn.close()
            return False
            
    def update_address(self, patient_id: int, street_address: str, city: str, state: str, zip_code: str) -> bool:
        """Update a patient's address information. Returns success status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update address information
            cursor.execute(
                "UPDATE patients SET street_address = ?, city = ?, state = ?, zip_code = ? WHERE id = ?",
                (street_address, city, state, zip_code, patient_id)
            )
            
            if cursor.rowcount == 0:
                logger.error(f"No patient found with ID: {patient_id}")
                conn.close()
                return False
                
            logger.info(f"Updated address for patient ID {patient_id}: {street_address}, {city}, {state} {zip_code}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating address: {e}")
            conn.close()
            return False
            
    def update_phone_number(self, patient_id: int, phone_number: str) -> bool:
        """Update a patient's phone number. Returns success status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update phone number
            cursor.execute(
                "UPDATE patients SET phone_number = ? WHERE id = ?",
                (phone_number, patient_id)
            )
            
            if cursor.rowcount == 0:
                logger.error(f"No patient found with ID: {patient_id}")
                conn.close()
                return False
                
            logger.info(f"Updated phone number for patient ID {patient_id}: {phone_number}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating phone number: {e}")
            conn.close()
            return False
            
    def update_email(self, patient_id: int, email: str) -> bool:
        """Update a patient's email address. Returns success status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update email address
            cursor.execute(
                "UPDATE patients SET email = ? WHERE id = ?",
                (email, patient_id)
            )
            
            if cursor.rowcount == 0:
                logger.error(f"No patient found with ID: {patient_id}")
                conn.close()
                return False
                
            logger.info(f"Updated email for patient ID {patient_id}: {email}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating email: {e}")
            conn.close()
            return False

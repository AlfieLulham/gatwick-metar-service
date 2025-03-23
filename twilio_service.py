import os
import logging
from twilio.rest import Client

# Configure logging
logger = logging.getLogger(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")  # Should be in format "whatsapp:+1234567890"

def send_whatsapp_message(to_number, message_body):
    """
    Send a WhatsApp message via Twilio.
    
    Args:
        to_number (str): The recipient's WhatsApp number in Twilio format (whatsapp:+1234567890)
        message_body (str): The message to send
    
    Returns:
        bool: True if the message was sent successfully, False otherwise
    """
    try:
        # Check if we have the required Twilio credentials
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
            logger.error("Missing Twilio credentials. Cannot send WhatsApp message.")
            return False
        
        # Initialize the Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Ensure the recipient number is in the correct format
        # If it doesn't already start with "whatsapp:", add it
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        
        # Ensure the from number is in the correct format
        from_number = TWILIO_WHATSAPP_NUMBER
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
        
        # Send the message
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        
        logger.debug(f"WhatsApp message sent with SID: {message.sid}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return False

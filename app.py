import os
import logging
from flask import Flask, request, render_template
from twilio_service import send_whatsapp_message
from metar_service import get_gatwick_metar, parse_metar_for_human

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint for incoming WhatsApp messages via Twilio.
    """
    try:
        # Get the message body from the request
        incoming_msg = request.values.get('Body', '').strip().lower()
        # Get the sender's WhatsApp number
        sender = request.values.get('From', '')
        
        logger.debug(f"Received message: '{incoming_msg}' from {sender}")
        
        # Simple message parsing - any message containing 'metar' or specific keywords triggers a response
        if 'metar' in incoming_msg or 'weather' in incoming_msg or 'gatwick' in incoming_msg:
            # Fetch the latest METAR for Gatwick
            try:
                metar_data = get_gatwick_metar()
                if metar_data:
                    # Parse the METAR into a more readable format
                    human_readable = parse_metar_for_human(metar_data)
                    # Send the formatted METAR response via WhatsApp
                    send_whatsapp_message(sender, human_readable)
                    logger.debug(f"Sent METAR response to {sender}")
                else:
                    # Handle case where no METAR data was returned
                    send_whatsapp_message(sender, "Sorry, I couldn't retrieve the Gatwick METAR data at the moment. Please try again later.")
                    logger.error("No METAR data returned from API")
            except Exception as e:
                # Handle errors in fetching or parsing METAR
                error_msg = f"Sorry, there was an error retrieving the Gatwick METAR: {str(e)}"
                send_whatsapp_message(sender, error_msg)
                logger.error(f"Error fetching METAR: {str(e)}")
        else:
            # If the message doesn't contain any trigger keywords, send a help message
            help_msg = ("To get the latest Gatwick Airport METAR information, "
                      "please send a message containing 'metar', 'weather', or 'gatwick'.")
            send_whatsapp_message(sender, help_msg)
            logger.debug(f"Sent help message to {sender}")
        
        # Twilio expects a TwiML response
        return '<Response></Response>'
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return '<Response></Response>', 500

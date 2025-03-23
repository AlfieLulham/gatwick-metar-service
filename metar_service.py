import os
import logging
import requests
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Aviation weather API configuration
# We'll use the CheckWX API which is a popular aviation weather data provider
CHECKWX_API_KEY = os.environ.get("CHECKWX_API_KEY")
CHECKWX_API_URL = "https://api.checkwx.com/metar/EGKK/decoded"  # EGKK is Gatwick's ICAO code

def get_gatwick_metar():
    """
    Fetch the latest METAR information for Gatwick Airport (EGKK).
    
    Returns:
        dict: The METAR data as a dictionary or None if there was an error
    """
    try:
        # If no API key, try using a fallback free API
        if not CHECKWX_API_KEY:
            logger.warning("No CheckWX API key found. Using fallback AVIATIONWEATHER.GOV API.")
            return get_gatwick_metar_fallback()
        
        headers = {"X-API-Key": CHECKWX_API_KEY}
        response = requests.get(CHECKWX_API_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results", 0) > 0:
                return data["data"][0]  # Return the first (latest) METAR
            else:
                logger.error("No METAR data found in API response")
                return None
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            # If primary API fails, try the fallback
            return get_gatwick_metar_fallback()
    
    except Exception as e:
        logger.error(f"Error fetching METAR data: {str(e)}")
        # If an exception occurs, try the fallback
        return get_gatwick_metar_fallback()

def get_gatwick_metar_fallback():
    """
    Fallback method to fetch METAR from AVIATIONWEATHER.GOV (no API key required).
    
    Returns:
        dict: The METAR data as a dictionary or None if there was an error
    """
    try:
        url = "https://aviationweather.gov/api/data/metar?ids=EGKK&format=json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]  # Return the first (latest) METAR
            else:
                logger.error("No METAR data found in fallback API response")
                return None
        else:
            logger.error(f"Fallback API request failed with status code {response.status_code}: {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error fetching fallback METAR data: {str(e)}")
        return None

def parse_metar_for_human(metar_data):
    """
    Parse the METAR data into a human-readable format.
    
    Args:
        metar_data (dict): The METAR data dictionary
    
    Returns:
        str: A formatted string containing the human-readable METAR information
    """
    try:
        # Format will depend on which API was used (CheckWX or fallback)
        # Check which format we're working with
        if "raw_text" in metar_data:
            # This is likely the fallback API format
            return parse_aviationweather_metar(metar_data)
        else:
            # This is likely the CheckWX API format
            return parse_checkwx_metar(metar_data)
    
    except Exception as e:
        logger.error(f"Error parsing METAR data: {str(e)}")
        # Return the raw METAR as a fallback
        if "raw_text" in metar_data:
            return f"Gatwick METAR: {metar_data['raw_text']}"
        elif "raw" in metar_data:
            return f"Gatwick METAR: {metar_data['raw']}"
        else:
            return "Sorry, I couldn't parse the METAR data properly."

def parse_checkwx_metar(metar_data):
    """Parse METAR data from CheckWX API format."""
    try:
        # Extract basic information
        raw_metar = metar_data.get("raw", "N/A")
        time = metar_data.get("observed", "N/A")
        
        # Extract weather conditions
        temp_c = metar_data.get("temperature", {}).get("celsius", "N/A")
        wind_speed = metar_data.get("wind", {}).get("speed_kts", "N/A")
        wind_direction = metar_data.get("wind", {}).get("degrees", "N/A")
        wind_gust = metar_data.get("wind", {}).get("gust_kts", "")
        visibility = metar_data.get("visibility", {}).get("meters", "N/A")
        
        # Convert visibility to km for readability
        visibility_km = f"{float(visibility)/1000:.1f} km" if visibility != "N/A" else "N/A"
        
        # Extract cloud information
        clouds = ""
        if "clouds" in metar_data and metar_data["clouds"]:
            cloud_layers = []
            for cloud in metar_data["clouds"]:
                code = cloud.get("code", "")
                altitude = cloud.get("base_feet_agl", "")
                if code and altitude:
                    cloud_layers.append(f"{code} at {altitude} ft")
            clouds = ", ".join(cloud_layers) if cloud_layers else "No cloud data"
        else:
            clouds = "No cloud data"
        
        # Format wind information
        wind_info = f"{wind_direction}° at {wind_speed} knots"
        if wind_gust:
            wind_info += f", gusting to {wind_gust} knots"
        
        # Build the response
        response = [
            f"🛫 *GATWICK AIRPORT (EGKK) METAR* 🛬",
            f"⏰ Observed: {time}",
            f"🌡️ Temperature: {temp_c}°C",
            f"💨 Wind: {wind_info}",
            f"👁️ Visibility: {visibility_km}",
            f"☁️ Clouds: {clouds}",
            f"📊 Raw METAR: {raw_metar}"
        ]
        
        return "\n\n".join(response)
    
    except Exception as e:
        logger.error(f"Error parsing CheckWX METAR: {str(e)}")
        # Return the raw METAR as a fallback
        return f"Gatwick METAR: {metar_data.get('raw', 'Data unavailable')}"

def parse_aviationweather_metar(metar_data):
    """Parse METAR data from AVIATIONWEATHER.GOV API format."""
    try:
        # Extract basic information
        raw_metar = metar_data.get("raw_text", "N/A")
        
        # Try to convert observation time
        obs_time = "N/A"
        if "observation_time" in metar_data:
            try:
                time_obj = datetime.strptime(metar_data["observation_time"], "%Y-%m-%dT%H:%M:%SZ")
                obs_time = time_obj.strftime("%d-%b-%Y %H:%M UTC")
            except:
                obs_time = metar_data["observation_time"]
        
        # Extract weather conditions
        temp_c = metar_data.get("temp_c", "N/A")
        wind_speed = metar_data.get("wind_speed_kt", "N/A")
        wind_direction = metar_data.get("wind_dir_degrees", "N/A")
        wind_gust = metar_data.get("wind_gust_kt", "")
        
        # Handle visibility
        visibility = "N/A"
        visibility_statute_mi = metar_data.get("visibility_statute_mi", "N/A")
        if visibility_statute_mi != "N/A":
            # Convert statute miles to km for international relevance
            try:
                visibility = f"{float(visibility_statute_mi) * 1.60934:.1f} km"
            except:
                visibility = f"{visibility_statute_mi} miles"
        
        # Extract cloud information
        clouds = "No cloud data"
        if "sky_condition" in metar_data:
            if isinstance(metar_data["sky_condition"], list):
                cloud_layers = []
                for cloud in metar_data["sky_condition"]:
                    code = cloud.get("sky_cover", "")
                    altitude = cloud.get("cloud_base_ft_agl", "")
                    if code and altitude:
                        cloud_layers.append(f"{code} at {altitude} ft")
                clouds = ", ".join(cloud_layers) if cloud_layers else "No cloud data"
            elif isinstance(metar_data["sky_condition"], dict):
                code = metar_data["sky_condition"].get("sky_cover", "")
                altitude = metar_data["sky_condition"].get("cloud_base_ft_agl", "")
                if code and altitude:
                    clouds = f"{code} at {altitude} ft"
        
        # Format wind information
        wind_info = f"{wind_direction}° at {wind_speed} knots"
        if wind_gust:
            wind_info += f", gusting to {wind_gust} knots"
        
        # Build the response
        response = [
            f"🛫 *GATWICK AIRPORT (EGKK) METAR* 🛬",
            f"⏰ Observed: {obs_time}",
            f"🌡️ Temperature: {temp_c}°C",
            f"💨 Wind: {wind_info}",
            f"👁️ Visibility: {visibility}",
            f"☁️ Clouds: {clouds}",
            f"📊 Raw METAR: {raw_metar}"
        ]
        
        return "\n\n".join(response)
    
    except Exception as e:
        logger.error(f"Error parsing AVIATIONWEATHER METAR: {str(e)}")
        # Return the raw METAR as a fallback
        return f"Gatwick METAR: {metar_data.get('raw_text', 'Data unavailable')}"

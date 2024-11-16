
#!/usr/bin/python3
# -*- coding:utf-8 -*-
import sys
import os

import config
API_KEY = config.API_KEY
DEV_ID = config.DEV_ID
stop_id = config.stop_id

print(API_KEY)
print(DEV_ID)
print(stop_id)

# Dynamically add the path to the waveshare_epd library
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'e-Paper/RaspberryPi_JetsonNano/python/lib')
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'e-Paper/RaspberryPi_JetsonNano/python/pic')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd2in13_V4
import time
from PIL import Image, ImageDraw, ImageFont
import traceback

import hmac
import binascii
import requests
from requests.exceptions import ConnectionError
import hashlib
import datetime
import threading

# Global variable to hold countdown seconds
countdown_seconds = 0

logging.basicConfig(level=logging.INFO)

def generate_signature(request_path, devid, api_key):
    request = f"{request_path}{'&' if '?' in request_path else '?'}devid={devid}"
    signature = hmac.new(api_key.encode('utf-8'), request.encode('utf-8'), hashlib.sha1).hexdigest()
    return f"http://timetableapi.ptv.vic.gov.au{request}&signature={signature}"

def get_departures_with_retry(api_key, devid, stop_id, route_type, limit=5, retries=3, delay=5):
    base_path = f"/v3/departures/route_type/{route_type}/stop/{stop_id}?max_results={limit}"
    complete_url = generate_signature(base_path, devid, api_key)
    print(f"Generated URL: {complete_url}")
    
    for attempt in range(retries):
        try:
            response = requests.get(complete_url)
            if response.status_code == 200:
                logging.info("Departures updated")
                return response.json()
            else:
                logging.error(f"Error: {response.status_code} - {response.text}")
                return None
        except ConnectionError as e:
            logging.error(f"Connection error: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)  # Wait before retrying
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return None
    logging.error(f"Max retries exceeded. Failed to get departures after {retries} attempts.")
    return None
    
def display_departures(departures):
    """
    Displays the upcoming departures in a readable format.
    
    :param departures: JSON response containing upcoming departures.
    """
    print("Upcoming Departures:")
    for departure in departures.get('departures', []):
        # Use the .get() method to avoid KeyErrors if a key doesn't exist
        line_id = departure.get('run_ref', 'Unknown Line')
        destination = departure.get('direction_id', 'Unknown Destination')  # Adjust this based on your data
        estimated_time = departure.get('estimated_departure_utc', 'Time Unknown')
        platform_number = departure.get('platform_number', 'No Platform Info')

        print(f"Line: {line_id}, Destination: {destination}, Estimated Departure: {estimated_time}, Platform: {platform_number}")

def display_countdown_to_next_departure(departures, destination_id=1):
    next_departure = None
    for departure in departures.get('departures', []):
        if departure.get('direction_id') == destination_id:
            next_departure = departure
            break

    if next_departure:
        estimated_time_str = next_departure.get('estimated_departure_utc')
        if estimated_time_str:
            estimated_time = datetime.datetime.fromisoformat(estimated_time_str[:-1]).replace(tzinfo=datetime.timezone.utc)
            current_time = datetime.datetime.now(datetime.timezone.utc)
            time_remaining = estimated_time - current_time
            countdown_seconds = int(time_remaining.total_seconds())
            if countdown_seconds > 0:
                return countdown_seconds
            else:
                return 0
        else:
            print("Estimated departure time is not available.")
    else:
        print(f"No upcoming departures found for destination {destination_id}.")
    return None

def api_polling_thread():
    global countdown_seconds
    last_api_call_time = time.time()

    while True:
        current_time = time.time()

        if current_time - last_api_call_time >= 30:  # Poll API every 30 seconds
            departures = get_departures_with_retry(API_KEY, DEV_ID, stop_id, route_type, retries=50, delay=20)
            if departures:
                display_departures(departures)
                countdown_seconds = display_countdown_to_next_departure(departures, destination_id=1)
            last_api_call_time = current_time

        time.sleep(1)

def display_thread():
    global countdown_seconds
    text_pos_set = 0
    
    while True:
        current_time = time.time()
        
        # Clear the entire screen before drawing new text
        time_draw.rectangle((0, 0, epd.height, epd.width), fill=255)
        
        if countdown_seconds is not None:
            # Update the display with the countdown time
            minutes, seconds = divmod(countdown_seconds, 60)
            countdown_text = f"{minutes:02}:{seconds:02}"
            
            if text_pos_set == 0:
                bbox = time_draw.textbbox((0, 0), countdown_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = ((epd.height - text_width) // 2, (epd.width - text_height) // 2)
                text_pos_set = 1
            
            time_draw.text(position, countdown_text, font=font, fill = 0)
            epd.displayPartial(epd.getbuffer(time_image))
            
            countdown_seconds -= 1  # Decrease countdown each second

        time.sleep(1)  # Update the display every second

try:
    epd = epd2in13_V4.EPD()
    logging.info("init and Clear")
    epd.init()
    epd.Clear(0xFF)
    logging.info("E-paper refresh")
    epd.init()
    time.sleep(2)

    # Drawing on the image
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 70)
    
    logging.info("Searching for stop ID")
    
    route_type = 0  # 0 for trains
        
    # Update the e-ink display every second with partial update
    logging.info("Show Time...")
    time_image = Image.new('1', (epd.height, epd.width), 255)
    time_draw = ImageDraw.Draw(time_image)
    
    epd.displayPartBaseImage(epd.getbuffer(time_image))
    
    # Start the API polling thread
    api_thread = threading.Thread(target=api_polling_thread)
    api_thread.daemon = True  # Allows thread to exit when main program exits
    api_thread.start()

    # Start the display update thread
    display_thread()
    
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd2in13_V4.epdconfig.module_exit(cleanup=True)
    exit()

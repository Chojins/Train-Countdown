import config
import hmac
import hashlib

API_KEY = config.API_KEY
DEV_ID = config.DEV_ID
stop_id = config.stop_id

import requests

def generate_signature(request_path, devid, api_key):
    request = f"{request_path}{'&' if '?' in request_path else '?'}devid={devid}"
    signature = hmac.new(api_key.encode('utf-8'), request.encode('utf-8'), hashlib.sha1).hexdigest()
    return f"http://timetableapi.ptv.vic.gov.au{request}&signature={signature}"

def get_train_routes_and_stops(api_key, devid):
    """
    Fetches all train routes and their stops (with stop IDs) from the PTV API and saves them to a file.
    :param api_key: Your PTV API key.
    :param devid: Your developer ID.
    :return: A dictionary of train routes with their stops (each stop includes name and ID).
    """
    # Fetch all train routes
    route_base_path = "/v3/routes"
    route_url = generate_signature(route_base_path, devid, api_key)
    
    response = requests.get(route_url)
    if response.status_code != 200:
        print(f"Error fetching routes: {response.status_code} - {response.text}")
        return None
    
    # Filter train routes
    all_routes = response.json().get('routes', [])
    train_routes = [route for route in all_routes if route.get('route_type') == 0]

    # Get stops for each train route
    routes_with_stops = {}
    for route in train_routes:
        route_id = route.get('route_id')
        route_name = route.get('route_name')
        print(f"Fetching stops for route: {route_name} (ID: {route_id})")
        
        stops_base_path = f"/v3/stops/route/{route_id}/route_type/0"
        stops_url = generate_signature(stops_base_path, devid, api_key)
        
        stops_response = requests.get(stops_url)
        if stops_response.status_code == 200:
            stops = stops_response.json().get('stops', [])
            routes_with_stops[route_name] = [
                {"stop_name": stop['stop_name'], "stop_id": stop['stop_id']} for stop in stops
            ]
        else:
            print(f"Error fetching stops for route {route_name}: {stops_response.status_code} - {stops_response.text}")

    # Save to file
    save_to_file(routes_with_stops, "train_stop_ids.txt")
    return routes_with_stops


def save_to_file(routes_with_stops, filename):
    """
    Saves the train routes and stops to a file in a readable format.
    :param routes_with_stops: Dictionary of train routes and their stops.
    :param filename: The name of the file to save the data to.
    """
    with open(filename, "w") as file:
        for route, stops in routes_with_stops.items():
            file.write(f"Route: {route}\n")
            for stop in stops:
                file.write(f"  - {stop['stop_name']} (ID: {stop['stop_id']})\n")
            file.write("\n")
    print(f"Data successfully saved to {filename}")
    
train_routes_and_stops = get_train_routes_and_stops(API_KEY, DEV_ID)
if train_routes_and_stops:
    print("Train routes and stops have been saved to train_stop_ids.txt.")
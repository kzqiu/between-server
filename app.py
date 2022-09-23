from flask import Flask, jsonify, request
from flask_cors import CORS
import googlemaps
from util.coords import haversine
import json

# Configuration
DEBUG = True;

# Instantiation
app = Flask(__name__)
app.config.from_object(__name__)

# Enable Google Maps API
# Private Serverside API Key, unrestricted!
gmaps = googlemaps.Client(key='enter your API key here')

# Enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

# location types: https://developers.google.com/maps/documentation/places/web-service/supported_types
loc_types = {'attractions': ['amusement_park', 'aquarium', 'book_store', 'library', 'movie_theater', 'night_club', 'park', 'shopping_mall', 'zoo'],
             'museums': ['art_gallery', 'museum'], 
             'food': ['bakery', 'bar', 'cafe', 'restaurant']}

# Sanity checking
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')

# utility
def get_lat_lng(data):
    return gmaps.geocode(data)[0]['geometry']['location']

# docs: https://googlemaps.github.io/google-maps-services-python/docs/index.html
@app.route('/places', methods=['POST'])
def get_nearby_places():
    response_object = {}
    post_data = request.get_json()

    # convert locations to geocodes
    pos1 = get_lat_lng(post_data['loc1'])
    pos2 = get_lat_lng(post_data['loc2'])

    # put coordinates in the geocode portion of response
    # formatted as: {'lat': 45.498276, 'lng': -122.6920349}
    response_object['geocodes'] = {'pos1': pos1, 'pos2': pos2} 

    # find nearby places and where they intersect
    # distance is in km!
    dist = round(haversine(response_object['geocodes']['pos1']['lng'], response_object['geocodes']['pos1']['lat'], \
        response_object['geocodes']['pos2']['lng'], response_object['geocodes']['pos2']['lat']), 3)
    
    response_object['dist'] = dist

    types = []
    places_found = []
    already_found = set()

    for t in post_data['types']:
        types += loc_types[t]

    for t in types: # distance is in meters!
        # get distances in meters, build some overlap in between the two radii
        rad = dist * 500 * 1.40

        p_temp = []

        res1 = gmaps.places_nearby(pos1, radius=rad, type=t)
        res2 = gmaps.places_nearby(pos2, radius=rad, type=t)

        if res1['status'] == 'ZERO_RESULTS' or res2['status'] == 'ZERO_RESULTS':
            continue

        encountered = {el['place_id'] for el in res1['results']}

        p_temp = [el for el in res2['results'] if el['place_id'] in encountered and el['place_id'] not in already_found]

        already_found.update(el['place_id'] for el in p_temp)

        places_found += p_temp

    response_object['places'] = json.dumps(places_found)
    print(json.dumps(places_found[0]))

    return response_object

if __name__ == "__main__":
    app.run()
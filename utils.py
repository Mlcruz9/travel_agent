import googlemaps
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")


# ---------------------------------------------------------
# 1. City Center Geocoding (cached)
# ---------------------------------------------------------
def get_city_center(_gmaps: googlemaps.Client, location_name: str):
    """Finds the geographic center coordinates of a given city."""
    print(f"--- Calling the Geocode API: {location_name} ---")

    try:
        geocode_result = _gmaps.geocode(location_name)
        if not geocode_result:
            return None, f"'{location_name}' could not be found on the map."

        coords = geocode_result[0].get("geometry", {}).get("location", None)
        return coords, None

    except Exception as e:
        return None, f"Geocode process failed: {str(e)}"


# ---------------------------------------------------------
# 2. Format price level as $ signs
# ---------------------------------------------------------
def format_price_level(price_level):
    """Converts Google price level integers into readable '$$' format."""
    if price_level is None:
        return ""
    if price_level == 0:
        return "Free"
    return "$" * int(price_level)


# ---------------------------------------------------------
# 3. Convert Google Places 'place' object into unified format
# ---------------------------------------------------------
def create_location_entry(place):
    """
    Formats a Google Places API result into a standardized dictionary
    for the map and travel agent output.
    """
    place_id = place.get("place_id")
    link = (
        f"https://www.google.com/maps/search/?api=1&query=Google&query_place_id={place_id}"
        if place_id else "#"
    )

    price_level = place.get("price_level")
    coords = place.get("geometry", {}).get("location", None)

    return {
        "name": place.get("name", "Unknown"),
        "rating": place.get("rating"),
        "price_label": format_price_level(price_level),
        "coords": coords,
        "link": link
    }
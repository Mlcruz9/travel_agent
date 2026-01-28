import os
import json
import googlemaps
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

from .utils import get_city_center, create_location_entry

openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

gmaps = googlemaps.Client(key=google_api_key)


# ---------------------------------------------------------
# 1. Deep dish finder (web search + LLM post-processing)
# ---------------------------------------------------------
@tool
def find_traditional_dishes_deep(city: str) -> str:
    """
    WEB SEARCH TOOL: Finds traditional local dishes for a given city.
    Uses Tavily + GPT-3.5 to extract a clean comma-separated list.
    """
    print(f"--- Performing deep culinary search for: {city} ---")

    try:
        search = TavilySearchResults()
        query = f"most famous 15 traditional local dishes, food, and desserts in {city}"
        results = search.run(query)

        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=openai_api_key)
        prompt = (
            f"Extract at least 10-15 famous local dishes from this text about {city}. "
            f"Return ONLY a comma-separated list:\n\n{results}"
        )

        response = llm.invoke(prompt)
        return response.content.strip()

    except Exception as e:
        return json.dumps({"error": f"Dish extraction failed: {str(e)}"})


# ---------------------------------------------------------
# 2. Enriched Discovery Plan (standard)
# ---------------------------------------------------------
@tool
def create_enriched_discovery_plan(city: str, dish_names: str) -> str:
    """
    Default discovery plan: general attractions + restaurants based on dishes.
    """
    print(f"--- Creating Enriched Plan with Links for {city} ---")

    city_center_coords, error = get_city_center(gmaps, city)
    if error:
        return json.dumps({"error": error})

    try:
        city_radius = 15000

        # Attractions
        attractions_raw = gmaps.places_nearby(
            location=city_center_coords,
            radius=city_radius,
            type="tourist_attraction"
        )
        attraction_suggestions = sorted(
            [p for p in attractions_raw.get("results", []) if p.get("user_ratings_total", 0) > 500],
            key=lambda x: x.get("user_ratings_total", 0),
            reverse=True
        )[:10]

        # Restaurants based on dishes
        dish_list = [d.strip() for d in dish_names.split(",")]
        all_restaurants = {}

        for dish in dish_list:
            if not dish:
                continue

            nearby = gmaps.places_nearby(
                location=city_center_coords,
                radius=city_radius,
                keyword=dish
            )

            for place in nearby.get("results", []):
                if place.get("place_id"):
                    all_restaurants[place["place_id"]] = place

        restaurant_suggestions = sorted(
            [p for p in all_restaurants.values() if p.get("rating") and p.get("user_ratings_total", 0) > 100],
            key=lambda x: x["rating"],
            reverse=True
        )[:10]

        if not attraction_suggestions and not restaurant_suggestions:
            return json.dumps({"error": f"No attractions or restaurants found in {city}."})

        anchor_place = attraction_suggestions[0] if attraction_suggestions else restaurant_suggestions[0]

        unified_plan = {
            "location": city,
            "city_center": {"name": f"{city} City Center", "coords": city_center_coords},
            "anchor_point": create_location_entry(anchor_place),
            "restaurant_suggestions": [create_location_entry(p) for p in restaurant_suggestions],
            "attraction_suggestions": [create_location_entry(p) for p in attraction_suggestions],
        }

        return json.dumps({"discovery_plan": unified_plan}, indent=2)

    except Exception as e:
        return json.dumps({"error": f"General plan failed: {str(e)}"})


# ---------------------------------------------------------
# 3. Budget-focused plan
# ---------------------------------------------------------
@tool
def create_budget_focused_plan(city: str, dish_names: str, budget: str) -> str:
    """
    Budget-sensitive discovery plan.
    """
    print(f"--- Creating BUDGET-FOCUSED Plan for {city} (Budget: {budget}) ---")

    city_center_coords, error = get_city_center(gmaps, city)
    if error:
        return json.dumps({"error": error})

    # Budget → price levels
    price_params = {}
    b = budget.lower()

    if "cheap" in b or "affordable" in b:
        price_params["max_price"] = 2
    elif "luxury" in b or "expensive" in b:
        price_params["min_price"] = 3

    try:
        city_radius = 15000

        # Attractions
        attractions_raw = gmaps.places_nearby(
            location=city_center_coords,
            radius=city_radius,
            type="tourist_attraction"
        )
        attraction_suggestions = sorted(
            [p for p in attractions_raw.get("results", []) if p.get("user_ratings_total", 0) > 500],
            key=lambda x: x.get("user_ratings_total", 0),
            reverse=True
        )[:5]

        # Restaurants with budget filters
        dish_list = [d.strip() for d in dish_names.split(",")]
        all_restaurants = {}

        for dish in dish_list:
            if not dish:
                continue

            search_params = {
                "location": city_center_coords,
                "radius": city_radius,
                "keyword": dish,
                "type": "restaurant",
                **price_params
            }

            nearby = gmaps.places_nearby(**search_params)

            for place in nearby.get("results", []):
                if place.get("place_id"):
                    all_restaurants[place["place_id"]] = place

        restaurant_suggestions = sorted(
            [p for p in all_restaurants.values() if p.get("rating") and p.get("user_ratings_total", 0) > 50],
            key=lambda x: x["rating"],
            reverse=True
        )[:7]

        if not restaurant_suggestions:
            return json.dumps({"error": f"No restaurants found in {city} for budget '{budget}'."})

        anchor = attraction_suggestions[0] if attraction_suggestions else restaurant_suggestions[0]

        unified_plan = {
            "location": city,
            "city_center": {"name": f"{city} City Center", "coords": city_center_coords},
            "anchor_point": create_location_entry(anchor),
            "restaurant_suggestions": [create_location_entry(p) for p in restaurant_suggestions],
            "attraction_suggestions": [create_location_entry(p) for p in attraction_suggestions],
        }

        return json.dumps({"discovery_plan": unified_plan}, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Budget plan failed: {str(e)}"})


# ---------------------------------------------------------
# 4. Interest-focused plan
# ---------------------------------------------------------
@tool
def create_interest_focused_plan(city: str, dish_names: str, interest: str) -> str:
    """
    Interest-sensitive discovery plan (art, history, nightlife, nature, etc.).
    """
    print(f"--- Creating INTEREST-FOCUSED Plan for {city} (Interest: {interest}) ---")

    city_center_coords, error = get_city_center(gmaps, city)
    if error:
        return json.dumps({"error": error})

    try:
        query = f"{interest} in {city}"
        city_radius = 25000

        places_result = gmaps.places(
            query=query,
            location=city_center_coords,
            radius=city_radius
        )

        # Filter out hotels
        filtered = []
        block_terms = ["hotel", "hostel", "apart", "residence", "inn"]

        for place in places_result.get("results", []):
            name = place.get("name", "").lower()
            if any(b in name for b in block_terms):
                continue
            filtered.append(place)

        attraction_suggestions = sorted(
            [p for p in filtered if p.get("user_ratings_total", 0) > 100],
            key=lambda x: x.get("user_ratings_total", 0),
            reverse=True
        )[:5]

        if not attraction_suggestions:
            return json.dumps({"error": f"No attractions match interest '{interest}' in {city}."})

        # Restaurants near first attraction
        anchor_coords = attraction_suggestions[0]["geometry"]["location"]

        dish_list = [d.strip() for d in dish_names.split(",")]
        all_restaurants = {}

        for dish in dish_list:
            if not dish:
                continue

            nearby = gmaps.places_nearby(
                location=anchor_coords,
                radius=2000,
                keyword=dish,
                type="restaurant"
            )

            for place in nearby.get("results", []):
                if place.get("place_id"):
                    all_restaurants[place["place_id"]] = place

        restaurant_suggestions = sorted(
            [p for p in all_restaurants.values() if p.get("rating") and p.get("user_ratings_total", 0) > 50],
            key=lambda x: x["rating"],
            reverse=True
        )[:7]

        unified_plan = {
            "location": city,
            "city_center": {"name": f"{city} City Center", "coords": city_center_coords},
            "anchor_point": create_location_entry(attraction_suggestions[0]),
            "restaurant_suggestions": [create_location_entry(p) for p in restaurant_suggestions],
            "attraction_suggestions": [create_location_entry(p) for p in attraction_suggestions],
        }

        return json.dumps({"discovery_plan": unified_plan}, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Interest plan failed: {str(e)}"})

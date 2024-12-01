import streamlit as st
import googlemaps
import openai
import pandas as pd
import json
import re
import ipywidgets as widgets
from IPython.display import display, Javascript
from streamlit_geolocation import streamlit_geolocation
#from streamlit_extras.button_selector import button_selector
#from streamlit_extras.app_logo import add_logo

st.set_page_config(page_title="Snap Review", page_icon="img/SnapReviewIcon.png")
st.image("img/SnapReviewIcon.png", caption=None)
st.title("Quick Google Review Summary")

# Initialize Google Maps and OpenAI clients
GOOGLE_API_KEY = st.secrets["GoogleMapsKey"]
OPENAI_API_KEY = st.secrets["OpenAIkey"]
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
openai.api_key = OPENAI_API_KEY

def fetch_reviews_summary(reviews):
    """Summarize reviews into Dating and Gathering categories using OpenAI."""
    if not reviews:
        return "No reviews available.", "No reviews available."

    review_texts = "\n".join([review.get("text", "") for review in reviews if review.get("text")])
    #print ("review_texts: ", review_texts)

    prompt = f"""
    Please summarize the information relevant to the category assigned to you.
    Summarize the following reviews into two categories:
    1. Dating Summary (focus on the experience for couples).
    2. Gathering Summary (focus on the experience for groups of friends or families).

    Please provide the summaries in the following JSON format:
    {{"Dating Summary": "your summary", "Gathering Summary": "your summary"}}

    Reviews:
    {review_texts}

    Keep your Dating Summary and your Gathering Summary under 50 words for each.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in providing summaries."},
                {"role": "user", "content": prompt}
            ],
            n=1,
            stop=None,
            temperature=0.7,
        )
        summary_str = response['choices'][0]['message']['content']

        match = re.search(r'\{(.*?)\}', summary_str, re.DOTALL)

        if match:
            summary_str = match.group(0)
        else:
            print("Could not find JSON in response.")
            return "Error: No JSON found.", "Error: No JSON found."

        summary = json.loads(summary_str)

        dating_summary = summary.get("Dating Summary", "No dating summary found.")
        gathering_summary = summary.get("Gathering Summary", "No gathering summary found.")



        return dating_summary, gathering_summary

    except Exception as e:
        return "Error summarizing reviews.", "Error summarizing reviews."

def search_and_summarize_restaurants(query, store_type, summary_type, get_location):
        
    if get_location:
        location = (get_location['latitude'], get_location['longitude'])
        radius = 20000  # Radius in meters (20km)
        st.write(f"Using user's location: {location}")
        st.write(f"Search for radius = {radius/1000} km")
    else:
        # Define a central location in Massachusetts (e.g., Boston)
        location = (42.3601, -71.0589)  # Latitude and Longitude of Boston, MA
        radius = 50000  # Radius in meters (50km)
        st.write(f"Search for Great Boston area")


    # Use the Places API to search for the restaurant
    results = gmaps.places(
        query=query,
        location=location,
        radius=radius,
        type=store_type
    )

    # Check for results
    if results and "results" in results:
        restaurants = results["results"][:5]
        final_data = []
        for restaurant in restaurants:
            name = restaurant.get("name")
            address = restaurant.get("formatted_address", "No address provided")
            rating = restaurant.get("rating", "No rating provided")
            total_reviews = restaurant.get("user_ratings_total", 0)
            place_id = restaurant.get("place_id")

            if place_id:
                # Get detailed reviews for each restaurant
                details = gmaps.place(place_id=place_id)
                reviews = details["result"].get("reviews", [])
                types = details["result"].get("types", []) # Get the type
                restaurant_type = types[0] if types else "No type provided" # Extract the first type

                st.write(f"Find reviews for {name}:")
                dating_summary, gathering_summary = fetch_reviews_summary(reviews)
            else:
                dating_summary = "No reviews available."
                gathering_summary = "No reviews available."

            # Append restaurant data
            final_data.append({
                "Restaurant Name": name,
                "Total Reviews": total_reviews,
                "Overall Rating": rating,
                #"Restaurant Type": restaurant_type,
                #"types": types,
                "Address": address,
                "Dating Summary": dating_summary,
                "Gathering Summary": gathering_summary
            })

        # Create and display the DataFrame
        df = pd.DataFrame(final_data)
        df = df.sort_values(by=['Overall Rating'], ascending=False)  # Sort by rating

        # Format 'Overall Rating' column to display 1 decimal place
        df['Overall Rating'] = df['Overall Rating'].map('{:.1f}'.format)

         # Filter columns based on summary_type
        if summary_type == "Dating":
          df = df.drop(columns=["Gathering Summary"])
        elif summary_type == "Gathering":
          df = df.drop(columns=["Dating Summary"])

        st.write("All Restaurants with Summaries (Ordered by Overall Rating):")
        st.write(df.style.hide(axis="index"))
    else:
        print("No results found.")

#store_type = ["Restaurant", "Bar", "Cafe"]
#selected_index = button_selector(store_type, index=0, spec=4, key="button_selector_place_type", label="What kind of place are you looking for?")
#st.write(f"Selected month: {store_type[selected_index]}")

store_type = st.selectbox(
    "I am looking for a ...",
    ("Restaurant", "Bar", "Cafe"),
    index=None,
    placeholder="Please select ...",
)

summary_type = st.selectbox(
    "For my purpose of ...",
    ("Dating", "Gathering", "Working", "Friends"),
    index=None,
    placeholder="Please select ...",
)

# Get user query
user_query = st.text_input("(Optional) Enter the name of the place if you're looking for specific place. (Ex. KFC, Mc Donald)")

if user_query:
    st.write("Please click the button to get your location: ")
    get_location = streamlit_geolocation()
else:
    get_location = None
    
# Get user requirements
def requirements():
    st.checkbox(["Wifi","Seating", "Patio", "Restroom", "Parking", "Private Space", "Pet-allow", "Accessibility"], value=True)
    st.write("👈 Check your requirements!")

if summary_type and summary_type:
    search_and_summarize_restaurants(user_query, store_type, summary_type, get_location)

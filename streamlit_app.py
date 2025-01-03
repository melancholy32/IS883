import streamlit as st
import googlemaps
import openai
import pandas as pd
import json
import re
import ipywidgets as widgets
from IPython.display import display, Javascript
from streamlit_js_eval import get_geolocation
# from langchain_community.utilities import GoogleSerperAPIWrapper
# from langchain_core.tools import Tool
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI
# from langchain.agents import AgentExecutor, create_tool_calling_agent
import os

#from streamlit_extras.button_selector import button_selector
#from streamlit_extras.app_logo import add_logo

st.set_page_config(page_title="Snap Review", page_icon="img/SnapReviewIcon.png")
st.image("img/SnapReviewIcon.png", caption=None)
st.title("Quick Google Review Summary")

tab_info, tab_search, tab_chatbot,  = st.tabs(
    ["🗒️ About this app", "🌐 Searching", "💬 Chatbot"]
)

# Initialize Google Maps and OpenAI clients
GOOGLE_API_KEY = st.secrets["GoogleMapsKey"]
OPENAI_API_KEY = st.secrets["OpenAIkey"]
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
openai.api_key = OPENAI_API_KEY


def fetch_reviews_summary(reviews):
    """Summarize reviews into different categories using OpenAI."""
    if not reviews:
        return "No reviews available.", "No reviews available.", "No reviews available."

    review_texts = "\n".join([review.get("text", "") for review in reviews if review.get("text")])

    prompt = f"""
        Please summarize the information relevant to the category assigned to you.
    Summarize the following reviews into two categories:
    1. Dating Summary (focus on the experience, atmosphere, cuisine, and service quality for couples).
    2. Gathering Summary (focus on the experience, location, accessibility, and seating for groups of friends or families).
    3. Remote Working Summary (focus on the Wi-Fi quality, power outlets, and noise level for people who are doing remote working).
    Please provide the summaries in the following JSON format:
    {{"Dating Summary": "your summary", "Gathering Summary": "your summary", "Remote Working Summary": "Remote Working Summary"}}
    Reviews:
    {review_texts}
    Keep your Summary under 80 words for each.
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
        remote_working_summary = summary.get("Remote Working Summary", "No remote working summary found.")


        return dating_summary, gathering_summary, remote_working_summary

    except Exception as e:
        return "Error summarizing reviews.", "Error summarizing reviews.", "Error summarizing reviews."

def search_and_summarize_restaurants(query, store_type, summary_type, get_location):

    if get_location:
        location = (get_location['coords']['latitude'], get_location['coords']['longitude'])
        radius = 20000  # Radius in meters (20km)
        st.markdown(f":gray[Using user's location: {location}]")
        st.markdown(f":gray[Search for radius = {radius/1000} km]")
    else:
        # Define a central location in Massachusetts (e.g., Boston)
        location = (42.3601, -71.0589)  # Latitude and Longitude of Boston, MA
        radius = 50000  # Radius in meters (50km)
        st.markdown(f":gray[Search for Great Boston area]")


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

                #st.write(f"Find reviews for {name}:")
                dating_summary, gathering_summary, remote_working_summary = fetch_reviews_summary(reviews)
            else:
                dating_summary = "No reviews available."
                gathering_summary = "No reviews available."
                remote_working_summary = "No reviews available."

            # Append restaurant data
            final_data.append({
                "Restaurant Name": name,
                "Total Reviews": total_reviews,
                "Overall Rating": rating,
                #"Restaurant Type": restaurant_type,
                #"types": types,
                "Address": address,
                "Dating Summary": dating_summary,
                "Gathering Summary": gathering_summary,
                "Remote Working Summary": remote_working_summary
            })

        # Create and display the DataFrame
        df = pd.DataFrame(final_data)
        df = df.sort_values(by=['Overall Rating'], ascending=False)  # Sort by rating

        # Format 'Overall Rating' column to display 1 decimal place
        df['Overall Rating'] = df['Overall Rating'].map('{:.1f}'.format)

         # Filter columns based on summary_type
        if summary_type == "💘 Dating":
          df = df.drop(columns=["Gathering Summary"])
          df = df.drop(columns=["Remote Working Summary"])
        elif summary_type == "👬 Gathering":
          df = df.drop(columns=["Dating Summary"])
          df = df.drop(columns=["Remote Working Summary"])
        elif summary_type == "💻 Working":
          df = df.drop(columns=["Dating Summary"])
          df = df.drop(columns=["Gathering Summary"])

        #st.write("All Restaurants with Summaries (Ordered by Overall Rating):")

        for index, row in df.iterrows():
          st.divider()
          for column, value in row.items():
            if column == 'Restaurant Name':
                st.header(f"{value}")
            elif column in ["Gathering Summary", "Dating Summary", "Remote Working Summary"]:
                st.markdown(f"**{column}:** :blue[{value}]")
            else:
                st.markdown(f"**{column}:** {value}")
          st.write()
    else:
        st.write("No results found.")

with tab_info:
    st.write("This app is to help you easily find places for your purposes from Google Review🔍. Save some time by using our app!😁")
    
    #store_type = ["🍽️ Restaurant", "🥂 Bar", "☕ Cafe"]
    #selected_index = button_selector(store_type, index=0, spec=4, key="button_selector_place_type", label="What kind of place are you looking for?")
    #st.write(f"Selected month: {store_type[selected_index]}")

with tab_search:
    store_type = st.selectbox(
        "🔍 I am looking for a ...",
        ("restaurant", "bar", "cafe"),
        index=None,
        placeholder="Please select ...",
    )

    summary_type = st.selectbox(
        "🔍 For my purpose of ...",
        ("💘 Dating", "👬 Gathering", "💻 Working"),
        index=None,
        placeholder="Please select ...",
    )

    # Get user query
    user_query = st.text_input("(Optional) Enter the name of the place if you're looking for a specific place. (Ex. KFC, Cafe Nero)")

    # Get user's location
    get_location = get_geolocation()

    if summary_type and summary_type:
        search_and_summarize_restaurants(user_query, store_type, summary_type, get_location)
        
with tab_chatbot:
    with st.form("restaurant_query_form"):  # Wrap everything in a form
        user_query = st.text_input("🔍 Which restaurant are you looking for?")
        
        # Add the submit button
        submitted = st.form_submit_button(
            "Search", use_container_width=True
        )
    
    if submitted:
        # Generate the instruction based on the user's input
        instruction = f"""
        Based on the user's query, please search for detailed information on that place(s) in Boston.
        1) Details to Provide:
        - Address
        - Website link (if available).
        - Phone number
        - Google rating
        3. Analyze and summarize the overall sentiment from reviews.
        Highlight the key strengths and potential drawbacks of the place. 
        Recommend whether the location is suited for:
        - Gatherings (consider factors like location, accessibility, seating, etc. for groups of friends or families)
        - Dating (consider factors like atmosphere, cuisine, service quality, etc. for couples)
        - Remote Working (consider factors like noise level, availability of outlets, Wi-Fi, etc.)
        
        User query: {user_query}
        """
        
        chat = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o-mini")
        
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful assistant"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"), # To be used by the agent for intermediate operations.
            ]
        )
        
        # Setting up the Serper tool
        os.environ["SERPER_API_KEY"] = st.secrets['SERPER_API']
        search = GoogleSerperAPIWrapper()
        tools = [
            Tool(
                name="GoogleSerper",
                func=search.run,
                description="Useful for when you need to look up some information on the internet.",
            )
        ]
        
        # Defining the agent
        agent = create_tool_calling_agent(chat, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        # Run the agent and display the result
        st.write(agent_executor.invoke({"input": instruction})["output"])

import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

# Page config
st.set_page_config(page_title="Snap Review", page_icon="img/SnapReviewIcon.png")
st.image("img/SnapReviewIcon.png", caption=None)
st.title("Quick Google Review Summary")

# Initialize the OpenAI model
openai_api_key = st.secrets["OPENAI_API_KEY"]
llm = ChatOpenAI(openai_api_key=openai_api_key)

# Session state setup for messages and model selection
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user input to session messages
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response from assistant using LangChain's ChatOpenAI model
    response = llm.generate(
        [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    )
    
    # Display the assistant's response
    st.session_state.messages.append({"role": "assistant", "content": response[0]["text"]})
    with st.chat_message("assistant"):
        st.markdown(response[0]["text"])

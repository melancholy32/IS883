import streamlit as st
from openai import OpenAI
from langchain.chains import RoutingChain

st.set_page_config(page_title="Snap Review", page_icon="img/SnapReviewIcon.png")
st.image("img/SnapReviewIcon.png", caption=None)
st.title("Quick Google Review Summary")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[{"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages],stream=True)
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})

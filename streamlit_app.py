import streamlit as st
py -m pip install -r requirements.txt

st.set_page_config(page_title="Snap Review", page_icon="img/SnapReviewIcon.png",)
st.image("img/SnapReviewIcon.png", caption=None, width=None, use_column_width=None, clamp=False, channels="RGB", output_format="auto", use_container_width=False)
st.title("Quick Google Review Summary")

import switch_page

switch_page("pages/page2.py")

import streamlit as st

st.set_page_config(page_title="Snap Review", page_icon="img/SnapReviewIcon.png",)
st.image("img/SnapReviewIcon.png", caption=None, width=None, use_column_width=None, clamp=False, channels="RGB", output_format="auto", use_container_width=False)
st.title("Quick Google Review Summary")

page=st.session_state
'''if there is no page automatically calls main'''
if "currentPage" not in page:
    page["currentPage"]="main"
if page["currentPage"]=="main":
    st.header("You are at main page")
    changePage=st.button("nextPage")
    if changePage:
        page["currentPage"]="secondPage"
        st.experimental_rerun()
if page["currentPage"]=="secondPage":
    st.header("You are at Second page")
    back=st.button("move back")
    if back:
        ''' moving to main page '''
        page["currentPage"]="main"
        st.experimental_rerun()Preformatted text

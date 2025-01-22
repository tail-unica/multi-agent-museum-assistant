import streamlit as st


def get_user_info():
    # Streamlit UI setup
    st.title("User Information (Anonymous)")
    st.write("How much do you know about sardinian history?")

    # Input fields

    knowledge = st.selectbox(
        "Enter your level of knowledge about sardinian history ",
        ("Low", "Medium", "High"),
    )
    age = st.selectbox(
        "Which age group do you belong to?",
        ("<15", "15-23", "23-30", "30-45", ">50"),
    )

    # Button to process input
    if st.button('Send Data'):
        # with st.spinner('Processing...'):
        st.session_state['knowledge'] = knowledge
        st.session_state['age'] = age
        st.session_state['load_orch_thrd'].join()
        st.session_state['orchestrator'].generator.set_rag_template(st.session_state)
        st.switch_page("pages/generation.py")


if __name__ == "__main__":
    get_user_info()


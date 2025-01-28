import streamlit as st
from init_questions_multilanguage import init_questions
from src.custom_style.style import add_logo


def get_user_info():
    # Streamlit UI setup
    st.title(init_questions[st.session_state['language']]["userinfo"])
    add_logo()

    # Input fields

    knowledge = st.selectbox(
        init_questions[st.session_state['language']]["knowledge level"],
        init_questions[st.session_state['language']]["knowledge_settings"],
    )
    age = st.selectbox(
        init_questions[st.session_state['language']]["age"],
        ("<15", "15-23", "23-30", "30-45", ">50"),
    )

    kd_idx = init_questions[st.session_state['language']]["knowledge_settings"].index(knowledge)
    # Button to process input
    if st.button('Send Data'):
        # with st.spinner('Processing...'):
        st.session_state['knowledge'] = init_questions['English']["knowledge_settings"][kd_idx]
        st.session_state['age'] = age
        st.session_state['load_orch_thrd'].join()
        st.session_state['orchestrator'].generator.set_rag_template(st.session_state)
        st.switch_page("pages/generation.py")


if __name__ == "__main__":
    get_user_info()


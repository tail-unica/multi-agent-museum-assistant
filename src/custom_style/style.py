# Apply global CSS to style the entire app
import streamlit as st

global_css = """
<style>
<div class="banner">
    <img src="https://cimallai.it/wp-content/uploads/2019/05/logo_cima-1.svg" alt="Banner Image">
</div>
<style>
    .banner {
        width: 160%;
        height: 200px;
        overflow: hidden;
    }
    .banner img {
        width: 100%;
        object-fit: cover;
    }
</style>
"""


def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(https://cimallai.it/wp-content/uploads/2019/05/logo_cima-1.svg);
                background-repeat: no-repeat;
                background-position: center 20px; /* Center the image both horizontally and vertically */
                padding-top: 120px;
                align-items: center;
            }

        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
            [data-testid="stHeader"] {
                background-image: url(https://cimallai.it/wp-content/uploads/2019/05/logo_cima-1.svg);
                background-position: center center; /* Center the image both horizontally and vertically */
                background-repeat: no-repeat;
                padding-top: 120px;
                width: 100%;
            }

        </style>
        """,
        unsafe_allow_html=True,
    )
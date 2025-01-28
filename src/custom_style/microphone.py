import streamlit as st

def add_audio_input():
    """
    Adds an audio input widget fixed at the bottom of the page with custom styling.
    Returns the uploaded audio file, if any.
    """
    # Custom CSS to fix the audio input at the bottom of the page
    st.markdown("""
        <style>
        .audio-input-container {
            position: fixed;
            bottom: 10px; /* Adjust spacing from bottom */
            left: 50%;
            transform: translateX(-50%);
            background-color: #f9f9f9; /* Optional: Background for visibility */
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 9999; /* Ensure it stays above other elements */
        }
        </style>
    """, unsafe_allow_html=True)

    # Place the audio input widget inside the fixed container
    st.markdown('<div class="audio-input-container">', unsafe_allow_html=True)
    audio_file = st.audio_input("Record your audio:")
    st.markdown('</div>', unsafe_allow_html=True)

    return audio_file

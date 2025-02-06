import os
import sys
import uuid

sys.path.append('src/agents')
from init_questions_multilanguage import init_questions
from src.agents.retriever import Retriever
from src.custom_style.style import add_logo
from src.agents.generation import Generator
from src.config import config as cfg
import streamlit as st
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx,get_script_run_ctx

#__import__('pysqlite3')
#sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

#os.system("pip install googletrans==4.0.0rc1")




class Orchestrator():
    def __init__(self):
        #super(Orchestrator, self).__init__()
        print("loading orchestrator")
        self.retriever = Retriever(cfg.urls, cfg.local_docs, cfg.embedding_model)
        self.generator = Generator(self.retriever, cfg.model_local)

    def reset_session(self):
        st.session_state['knowledge'] = ""
        st.session_state['age'] = ""


def load_orchestrator(session_state):
    orchestrator = Orchestrator()
    session_state['orchestrator'] = orchestrator
    print("Orchestrator loaded")


def start_session(session_state):
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []

    session_state['knowledge'] = ""
    session_state['age'] = ""

    option = st.selectbox(
        "Scegli la tua lingua / Choose your Language / Choisissez votre langue / Wählen Sie Ihre Sprache",
        ("Italian", "English", "French", "German"),
    )

    session_state['language'] = option
    #st.write("You selected:", option)
    os.makedirs("../chats_history", exist_ok=True)
    # orchestrator = Orchestrator()

    if st.button(init_questions[st.session_state['language']]["send_data"]):
        st.session_state['load_orch_thrd'].start()
        #print(option)
        #print(st.session_state)
        st.switch_page("pages/profiling.py")


if __name__ == "__main__":
    st.set_page_config(initial_sidebar_state="collapsed")
    # Inject the global CSS styles
    # Display the custom HTML
    #st.components.v1.html(global_css)
    add_logo()



    ctx = get_script_run_ctx()

    load_orchestrator_thread = threading.Thread(target=load_orchestrator, name="load_orchestrator", args=[st.session_state], daemon=True)
    add_script_run_ctx(load_orchestrator_thread, ctx)

    start_session_thread = threading.Thread(target=start_session, name="start_session", args=[st.session_state], daemon=True)
    add_script_run_ctx(start_session_thread, ctx)

    st.session_state['load_orch_thrd'] = load_orchestrator_thread
    st.session_state['cheered'] = False


    #load_orchestrator_thread.start()
    start_session_thread.start()

    #load_orchestrator_thread.join()
    start_session_thread.join()



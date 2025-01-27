import sys
sys.path.append('src/agents')
import whisper
from TTS.api import TTS
from init_questions_multilanguage import init_questions
from src.agents.retriever import Retriever
from src.agents.profiling import get_user_info
from src.agents.generation import Generator
from src.config import config as cfg
import streamlit as st
import sys
import concurrent.futures
import threading
from multiprocessing import Process
from streamlit_chromadb_connection.chromadb_connection import ChromadbConnection
from streamlit.runtime.scriptrunner import add_script_run_ctx,get_script_run_ctx

#__import__('pysqlite3')
#sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')


chroma_db_config = {
    "client": "PersistentClient",
    "timeout": 20,
    "path": "../tmp/chroma"
}

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
    session_state['knowledge'] = ""
    session_state['age'] = ""
    conn = st.connection(name="persistent_chromadb",
                         type=ChromadbConnection,
                         **chroma_db_config)

    option = st.selectbox(
        "Scegli la tua lingua / Choose your Language / Choisissez votre langue / Wählen Sie Ihre Sprache",
        ("Italian", "English", "French", "German"),
    )

    session_state['language'] = option
    #st.write("You selected:", option)

    # orchestrator = Orchestrator()

    if st.button('Continue'):
        st.session_state['load_orch_thrd'].start()
        print(option)
        print(st.session_state)
        st.switch_page("pages/profiling.py")


if __name__ == "__main__":
    st.set_page_config(initial_sidebar_state="collapsed")
    ctx = get_script_run_ctx()

    load_orchestrator_thread = threading.Thread(target=load_orchestrator, name="load_orchestrator", args=[st.session_state], daemon=True)
    add_script_run_ctx(load_orchestrator_thread, ctx)

    start_session_thread = threading.Thread(target=start_session, name="start_session", args=[st.session_state], daemon=True)
    add_script_run_ctx(start_session_thread, ctx)

    st.session_state['load_orch_thrd'] = load_orchestrator_thread


    #load_orchestrator_thread.start()
    start_session_thread.start()

    #load_orchestrator_thread.join()
    start_session_thread.join()



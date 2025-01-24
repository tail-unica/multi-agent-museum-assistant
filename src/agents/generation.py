import gc
import time

import torch
from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import streamlit as st
from streamlit.components.v1 import components
from src.custom_style.microphone import html_code as mic_html
from init_questions_multilanguage import init_questions
import whisper
import pyttsx3

languages = {
    "English": "en",
    "French": "fr",
    "Italian": "it",
    "German": "de"
}

def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


class Generator():
    def __init__(self, retriever, model_local):
        #super(Generator, self).__init__()
        self.retriever = retriever
        self.retriever._init_retriever()
        #self.retriever.retriever = self.retriever.retriever.as_retriever()
        self.model_local = Ollama(model=model_local)
        self.user_data = None
        self.after_rag_template = """Answer the question based only on the following context:
        {context}. If the question does not match the context, just say that you don't know.  
        Question: {question}
        """


    def get_answer(self, question):
        if self.retriever.retriever.__class__.__name__ != "VectorStoreRetriever":
            self.retriever.retriever = self.retriever.retriever.as_retriever()
        after_rag_prompt = ChatPromptTemplate.from_template(self.after_rag_template)
        after_rag_chain = (
                {"context": self.retriever.retriever, "question": RunnablePassthrough()}
                | after_rag_prompt
                | self.model_local
                | StrOutputParser()
        )
        return after_rag_chain.invoke(question)

    def format_history(self, history):
        if history == "None":
            return ""
        hst = ""
        msg = history[-1]
        s = f"{msg['role']}: {msg['content']}\n"
        hst += s
        return hst

    def set_rag_template(self, history = "None"):

        self.after_rag_template = """You are a local guide at the CIMA museum, and it is your duty to provide enjoyable and complete answers to the visitors, using only words that are easy to translate in other languages.
            Answer the question based only on the following context:
        {context}. If the question does not match the context, just say that you don't know or that is not related to the museum. 
        Otherwise, provide very insightful answers, including all you know about the question and possible related contents. Do not mention the documents you read, just say all you know as if it was your knowledge.
        Question: {question}
        Remember that the visitor is already inside the museum, so try to suggest other operas inside it (while mentioning their location).
        """
        print(f"Template set to : {self.after_rag_template}!")



    def translate(self, text, language):
        prompt = (f"Translate in {language}, the following text : {text}. "
                  f"Translate ALL ENGLISH WORDS. Do not mention the fact that you translated it, just get the proper translation.")
        translated = self.model_local(prompt=prompt)
        return translated

if __name__ == "__main__":
    # Streamlit UI setup
    if 'orchestrator' in st.session_state:

        st.title(init_questions[st.session_state['language']]["title"])

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


        transcription = None


        # React to user input
        if prompt := st.chat_input(init_questions[st.session_state['language']]["query template"]) or transcription:
            #prompt = transcription["text"]
            transcription = None
            print(prompt)
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            if st.session_state['language'] != "English":
                prompt = st.session_state['orchestrator'].generator.translate(prompt, language="English")

            response = st.session_state['orchestrator'].generator.get_answer(str(prompt))

            if st.session_state['language'] != "English":
                response = st.session_state['orchestrator'].generator.translate(response, language=st.session_state['language'])

            torch.cuda.empty_cache()  # Clear unused GPU memory
            gc.collect()

            st.session_state['orchestrator'].tts = st.session_state['orchestrator'].tts.to("cuda:0")
            wav = st.session_state['orchestrator'].tts.tts_to_file(text=response,
                                                                   speaker_wav="../Paris symbolise la c.m4a",
                                                                   file_path="output.wav",
                                                                   language=languages[st.session_state['language']])
            st.session_state['orchestrator'].tts = st.session_state['orchestrator'].tts.to("cpu")
            torch.cuda.empty_cache()  # Clear unused GPU memory
            gc.collect()

            st.audio("output.wav", format="audio/mpeg", loop=False, autoplay=True)

            with st.chat_message("assistant"):
                response = st.write_stream(response_generator(response))

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

            torch.cuda.empty_cache()  # Clear unused GPU memory
            gc.collect()


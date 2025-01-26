import gc
import os
import re
import time

import torch
from gtts import gTTS
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
from googletrans import Translator


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
    def __init__(self, retriever, model_local, translator_model):
        #super(Generator, self).__init__()
        self.retriever = retriever
        self.retriever._init_retriever()
        self.model_local_name = model_local
        self.model_local = Ollama(model=self.model_local_name)
        self.translator = Translator()
        self.tts = gTTS
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
        Otherwise, provide insightful answers, including all you know about the question and possible related contents (only among the ones mentioned in the provided context). Do not mention the documents you read, just say all you know as if it was your knowledge.
        Question: {question}
        Remember that the visitor is already inside the museum, so try to suggest other operas inside it (while mentioning their location), but only among the ones mentioned in the provided context.
        """
        print(f"Template set to : {self.after_rag_template}!")



    def translate(self, text, source_lan, dest_lan):
        translated = self.translator.translate(text, src=source_lan, dest=dest_lan)
        return translated.text

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

        audio_support = False
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
                prompt = st.session_state['orchestrator'].generator.translate(prompt, languages[st.session_state['language']], "en")

            response = st.session_state['orchestrator'].generator.get_answer(str(prompt))
            # Regular expression to remove everything between <think> and </think>
            cleaned_text = re.sub(r"<think>.*?</think>", "", response)
            # Remove extra spaces (optional)
            response = " ".join(cleaned_text.split())

            if st.session_state['language'] != "English":
                response = st.session_state['orchestrator'].generator.translate(response, "en", languages[st.session_state['language']])


            if audio_support or True:
                speak = st.session_state['orchestrator'].generator.tts(text=response, lang=languages[st.session_state['language']], slow=False)
                #del st.session_state['orchestrator'].generator.model_local
                #torch.cuda.empty_cache()  # Clear unused GPU memory
                #gc.collect()

                #print(os.getcwd())
                #st.session_state['orchestrator'].tts = st.session_state['orchestrator'].tts.to("cuda:0")
                #wav = st.session_state['orchestrator'].tts.tts_to_file(text=response,
                                                                       #speaker_wav="../voice_samples/female_voice.m4a",
                                                                       #file_path="output.wav",
                                                                       #language=languages[st.session_state['language']])
                #st.session_state['orchestrator'].tts = st.session_state['orchestrator'].tts.to("cpu")


                #torch.cuda.empty_cache()  # Clear unused GPU memory
                #gc.collect()
                #st.session_state['orchestrator'].generator.model_local = Ollama(model=st.session_state['orchestrator'].generator.model_local_name)
                speak.save("output.mp3")
                st.audio("output.mp3", format="audio/mpeg", loop=False, autoplay=True)

            with st.chat_message("assistant"):
                response = st.write_stream(response_generator(response))

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

            torch.cuda.empty_cache()  # Clear unused GPU memory
            gc.collect()


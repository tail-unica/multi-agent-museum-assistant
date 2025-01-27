import copy
import gc
import os
import re
import time
import deepl
import torch
from gtts import gTTS
from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import streamlit as st
from streamlit.components.v1 import components
from src.custom_style.microphone import add_audio_input
from init_questions_multilanguage import init_questions
import whisper
import pyttsx3
from googletrans import Translator
from src.api import api_key
from src.config import config as cfg



def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


class Generator():
    def __init__(self, retriever, model_local):
        #super(Generator, self).__init__()
        self.retriever = retriever
        self.retriever._init_retriever()
        self.model_local_name = model_local
        self.model_local = Ollama(model=self.model_local_name)
        self.translator = Translator()
        self.deepl_translator = deepl.Translator(api_key)
        self.tts = gTTS
        self.user_data = None
        self.after_rag_template = """Answer the question based only on the following context:
        {context}. If the question does not match the context, just say that you don't know.  
        Question: {question}
        """


    def get_answer(self, question):
        results, metadata = None, None
        if self.retriever.retriever.__class__.__name__ != "VectorStoreRetriever":
            self.retriever.retriever = self.retriever.retriever.as_retriever()

        after_rag_prompt = ChatPromptTemplate.from_template(self.after_rag_template)
        after_rag_chain = (
                {"context": self.retriever.retriever, "question": RunnablePassthrough()}
                | after_rag_prompt
                | self.model_local
                | StrOutputParser()
        )

        results = self.retriever.retriever.vectorstore.similarity_search_with_score(question)
        print(results)
        if results:
            metadata = results[0][0].metadata
            if results[0][1] > 750:
                metadata = None

        return after_rag_chain.invoke(question), metadata

    def format_history(self, history):
        if history == "None":
            return ""
        hst = ""
        msg = history[-1]
        s = f"{msg['role']}: {msg['content']}\n"
        hst += s
        return hst

    def set_rag_template(self, user_data=None):
        if user_data["age"] != "" and user_data["knowledge"] != "":
            self.user_data = user_data

        customization = f"**Customization for visitor profile**: Adjust your answer to match the visitor's characteristics:\n"\
        f"- **Age group**: {self.user_data['age']}\n"\
        f"- **Knowledge of Sardinian history**: {self.user_data['knowledge']}\n"\
        "Use the following guidelines to adapt your response:\n"\
        "1. **Age customization**:\n"\
        "   - Under 15: Keep it simple and fun, use storytelling and analogies.\n"\
        "   - 15-23: Relatable and casual tone, highlight exciting or mysterious elements.\n"\
        "   - 23-30: Balanced tone, focus on cultural connections and clarity.\n"\
        "   - 30-45: Warm and professional, highlight meaningful insights.\n"\
        "   - Over 50: Formal and respectful, focus on historical depth and traditions.\n"\
        "2. **Knowledge customization**:\n"\
        "   - Low: Focus on foundational and essential information.\n"\
        "   - Medium: Add contextual depth and comparisons.\n"\
        "   - High: Provide nuanced, advanced details and cultural connections.\n"\

        self.after_rag_template = """You are a local guide at the CIMA museum, and it is your duty to provide enjoyable and complete answers to the visitors, using only words that are easy to translate in other languages.
            Answer the question based only on the following context:
        {context}. If the question does not match the context, just say that you don't know or that is not related to the museum. DO NOT HALLUCINATE or invent/mention anything that is not provided in the context.
        Otherwise, provide insightful answers, including all you know about the question and possible related contents (only among the ones mentioned in the provided context). Do not mention the documents you read, just say all you know as if it was your knowledge.
        """ + customization + """
        Question: {question}
        Remember that the visitor is already inside the museum, so try to suggest other operas inside it (while mentioning their location), but only among the ones mentioned in the provided context. If some metadata about the answer is available, return it as photo_path = metadata
        """
        print(f"Template set to : {self.after_rag_template}!")



    def translate(self, text, source_lan, dest_lan):

        try:
            translated = self.deepl_translator.translate_text(text, target_lang=dest_lan.upper())
        except Exception as e:
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

        audio_support = True
        transcription = None

        audio_file = None #add_audio_input() #st.audio_input("Record a voice message")
        if audio_file is not None:
            #st.audio(audio_file, format="audio/wav")
            with open("temp_audio.wav", "wb") as f:
                f.write(audio_file.getbuffer())

            model = whisper.load_model("small", device="cuda:0")
            transcription = model.transcribe("temp_audio.wav", language=cfg.languages[st.session_state['language']], patience=2,
                                                                            beam_size=5)
            del model
            torch.cuda.empty_cache()  # Clear unused GPU memory
            gc.collect()


        # React to user input
        if prompt := st.chat_input(init_questions[st.session_state['language']]["query template"]) or transcription:
            #prompt = transcription["text"]
            #transcription = None
            print(prompt)
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            if st.session_state['language'] != "English":
                prompt = st.session_state['orchestrator'].generator.translate(prompt, cfg.languages[st.session_state['language']], "en")

            print(prompt)

            response, metadata = st.session_state['orchestrator'].generator.get_answer(str(prompt))
            print(metadata)
            # Regular expression to remove everything between <think> and </think>
            cleaned_text = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
            # Remove extra spaces (optional)
            response = " ".join(cleaned_text.split())

            if st.session_state['language'] != "English":
                response = st.session_state['orchestrator'].generator.translate(response, "en", cfg.languages[st.session_state['language']])


            if audio_support:
                speak = st.session_state['orchestrator'].generator.tts(text=response, lang=cfg.languages[st.session_state['language']], slow=False)
                speak.save("output.mp3")
                st.audio("output.mp3", format="audio/mpeg", loop=False, autoplay=False)

            with st.chat_message("assistant"):
                response = st.write_stream(response_generator(response))

            if metadata:
                caption = ""
                img = metadata["foto"]
                try:
                    caption = metadata['caption']
                except:
                    pass
                if img != "Not Available":
                    st.image(img, caption=caption, use_container_width=True)



            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

            torch.cuda.empty_cache()  # Clear unused GPU memory
            gc.collect()


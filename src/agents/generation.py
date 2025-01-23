import time

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

    def set_rag_template(self, user_data):
        if user_data["age"] != "" and user_data["knowledge"] != "":
            self.user_data = user_data
            self.after_rag_template = """You are a local guide at the CIMA museum, and it is your duty to provide enjoyable and complete answers to the visitors.
            Answer the question based only on the following context:
        {context}. If the question does not match the context, just say that you don't know or that is not related to the museum. 
        Provide very insightful answers, including all you know about the question and possible related contents. Do not mention the documents you read, just say all you know as if it was your knowledge
        Question: {question}
        """
        if user_data["language"] != "":
            self.after_rag_template = self.after_rag_template + f"Translate your answer in {user_data['language']}. Do not say anything about the fact that you translated the text."


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
        '''
        audio_file = st.audio_input("Record a voice message")
        if audio_file is not None:
            st.audio(audio_file, format="audio/wav")
            with open("temp_audio.wav", "wb") as f:
                f.write(audio_file.getbuffer())

            #model = whisper.load_model("small", device="cuda:0")
            transcription = st.session_state['orchestrator'].stt.transcribe("waa.wav", language="it", patience=2, beam_size=5)
            #st.write("Transcription:", transcription['text'])
        '''

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

            response = st.session_state['orchestrator'].generator.get_answer(str(prompt))

            wav = st.session_state['orchestrator'].tts.tts_to_file(text=response, speaker_wav="audio_response.wav")
            st.audio("output.wav", format="audio/mpeg", loop=False, autoplay=True)
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                #st.markdown(response)
                response = st.write_stream(response_generator(response))
                #st.session_state["orchestrator"].text_to_speech(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})


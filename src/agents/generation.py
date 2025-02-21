import copy
import gc
import json
import os
import re
import time
import deepl
import numpy as np
import requests
import torch
from gtts import gTTS
from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import streamlit as st
from langchain_community import embeddings

from init_questions_multilanguage import init_questions
from src.api import api_key
from src.config import config as cfg
from src.custom_style.style import add_logo


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
        self.deepl_translator = deepl.Translator(api_key)
        self.tts = gTTS
        self.user_data = None
        self.after_rag_template = """Answer the question based only on the following context:
        {context}. If the question does not match the context, just say that you don't know.  
        Question: {question}
        """

    def normalize_vector(self, vector):
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector  # Handle edge case for zero vector
        return vector / norm

    def format_context(self, results, max_docs=5):
        # Limit to top N documents (optional)
        filtered_results = results[:max_docs]

        # Format the context by extracting document content
        context_parts = [f"Document {i + 1}: {doc.page_content.strip()}" for i, (doc, score) in
                         enumerate(filtered_results)]

        # Join all document contents into a single context string
        return "\n\n".join(context_parts)

    def get_answer(self, question, last_message=""):
        results, metadata = None, None
        if self.retriever.retriever.__class__.__name__ != "VectorStoreRetriever":
            self.retriever.retriever = self.retriever.retriever.as_retriever()

        after_rag_prompt = ChatPromptTemplate.from_template(self.after_rag_template)
        print(f"Prompt: {after_rag_prompt}")

        #query_embedding = embeddings.OllamaEmbeddings(model="bge-m3").embed_query(question)
        #normalized_query_embedding = self.normalize_vector(query_embedding)

        results = self.retriever.retriever.vectorstore.similarity_search_with_score(question)

        scores = [ans[1] for ans in results]
        print(f"Retrieved scores: {scores}")
        cleared_ = [ans for ans in results if ans[1] < 0.55]
        context = self.format_context(cleared_)
        print("Context: ", context)

        # print(results)
        if results:
            metadata = results[0][0].metadata
            if results[0][1] > 0.55:
                metadata = None

        input_data = {"context": context, "question": question, "history": last_message}

        after_rag_chain = (
                {"context": RunnablePassthrough(), "question": RunnablePassthrough(), "history": RunnablePassthrough()}
                | after_rag_prompt
                | self.model_local
                | StrOutputParser()
        )



        return after_rag_chain.invoke(input_data), metadata

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
        "   - Under 15: Keep it simple and fun, use analogies were they stick to the context.\n"\
        "   - 15-23: Relatable and casual tone, highlight exciting or mysterious elements.\n"\
        "   - 23-30: Balanced tone, focus on cultural connections and clarity.\n"\
        "   - 30-45: Warm and professional, highlight meaningful insights.\n"\
        "   - Over 50: Formal and respectful, focus on historical depth and traditions.\n"\
        "2. **Knowledge customization**:\n"\
        "   - Low: Focus on foundational and essential information.\n"\
        "   - Medium: Add contextual depth and comparisons.\n"\
        "   - High: Provide nuanced, advanced details and cultural connections.\n"\

        self.after_rag_template = """You are a local guide at the CIMA museum, and it is your duty to provide enjoyable and complete answers to the visitors, using only words that are easy to understand.
            Answer the question based only on the following context:
        {context} and the last message you wrote {history}. If the question does not match the context, just say that it is not related to the museum. Avoid hallucinating or inventing/mention anything that is not related to the context.
        Otherwise, provide insightful answers, using only information's matching the context, the eventual history and the question. Do not mention the documents you read, just say all you know as if it was your knowledge.
        Answer only the question, avoiding inappropriate or useless addictions to the answer. If the user tells something about the last message you wrote, try to understand what he is asking about.
        """ + customization + """
        Question: {question}
        Opera and musical works are not part of the museum, so do not talk about them.
        The museum is open and full of sardinian history operas. If an user asks about opening times for the museum, just say the opening times and no more.
        Remember that the visitor is already inside the museum, so try to suggest other operas inside it (while mentioning their location), but only among the ones mentioned in the provided context.
        """
        #print(f"Template set to : {self.after_rag_template}!")

    def translate_locally(self, text, source_lang, target_lang):
        '''
        tokernizer_local = copy.deepcopy(self.tokenizer)
        tokernizer_local.tgt_lang = target_lang

        inputs = tokernizer_local(text, return_tensors="pt")#.to("cuda:0")
        if torch.cuda.is_available():
            inputs = inputs.to("cuda:0")

        generated_tokens = self.translator_local.generate(**inputs)
        translated_text = tokernizer_local.batch_decode(generated_tokens, skip_special_tokens=True)

        return translated_text[0]
        '''
        url = "http://localhost:2048/translate"
        data = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang
        }

        # Send the POST request
        response = requests.post(url, json=data)

        # Check for a successful response
        if response.status_code == 200:
            translated_text = response.json().get("translated_text")
            translated_text = translated_text.replace(".", ". ")
            translated_text = translated_text.replace("sardina", "sarda")

        else:
            translated_text = "Server not available. Please try again later."
        return translated_text

    def translate(self, text, source_lan, dest_lan):

        try:
            print("Deepl")
            if dest_lan == "en":
                dest_lan = "en-us"
            translated = self.deepl_translator.translate_text(text, target_lang=dest_lan.upper()).text
        except Exception as e:
            print("Local")
            if dest_lan == "en-us":
                dest_lan = "en"
            translated = self.translate_locally(text, source_lan, dest_lan)
            #translated = self.gtranslate(text, target_lang=dest_lan)

        return translated

if __name__ == "__main__":
    # Streamlit UI setup

    add_logo()
    if 'orchestrator' in st.session_state:

        last_answer = None
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

        if not st.session_state['cheered']:
            welcome_message = "Welcome to the CIMA museum in Allai! :) How can I help  you?"
            if st.session_state['language'] != "English":
                welcome_message = st.session_state['orchestrator'].generator.translate(welcome_message, "en", cfg.languages[st.session_state['language']])

            with st.chat_message("assistant"):
                st.write_stream(response_generator(welcome_message))
            st.session_state['cheered'] = True


        # React to user input
        if prompt := st.chat_input(init_questions[st.session_state['language']]["query template"]) or transcription:
            #prompt = transcription["text"]
            #transcription = None
            #print(prompt)
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            if st.session_state['language'] != "English":

                prompt = st.session_state['orchestrator'].generator.translate(prompt, cfg.languages[st.session_state['language']], "en")
                print(prompt)

            #print(prompt)
            with st.spinner(init_questions[st.session_state['language']]["think"]):

                response, metadata = st.session_state['orchestrator'].generator.get_answer(str(prompt), last_answer if last_answer else "None")
            #print(metadata)
            # Regular expression to remove everything between <think> and </think>
            cleaned_text = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
            # Remove extra spaces (optional)
            response = " ".join(cleaned_text.split())

            response = response.split("Answer:")[0]

            response = response.replace("Mениh", "menhir")
            response = response.replace("mhenry", "menhir")
            response = response.replace("betylr", "betile")

            last_answer = response

            if st.session_state['language'] != "English":
                #with st.spinner(init_questions[st.session_state['language']]["translating"]):
                print(response)
                response = response.replace("betyle", "betile")
                response = st.session_state['orchestrator'].generator.translate(response, "en", cfg.languages[st.session_state['language']])


            if audio_support:
                speak = st.session_state['orchestrator'].generator.tts(text=response.replace("*", ""), lang=cfg.languages[st.session_state['language']], slow=False)
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


            with open(f"../chats_history_{st.session_state.session_id}.json", "w") as f:
                json.dump(st.session_state.messages, f, indent=4)

            torch.cuda.empty_cache()  # Clear unused GPU memory
            gc.collect()


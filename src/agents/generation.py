import time

from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import streamlit as st
from init_questions_multilanguage import init_questions

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
        Give the answer considering that the user is """+self.user_data["age"]+""" years old and his/her knowledge about sardininan history is """+self.user_data["knowledge"]+""".
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


        # React to user input
        if prompt := st.chat_input(init_questions[st.session_state['language']]["query template"]):
            print(prompt)
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            response = st.session_state['orchestrator'].generator.get_answer(str(prompt))

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                #st.markdown(response)
                response = st.write_stream(response_generator(response))
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})


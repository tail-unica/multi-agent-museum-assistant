import json
import os
import time
import streamlit as st
import deepl
from langchain_community.document_loaders import WebBaseLoader # for web documents
from langchain_community.document_loaders import DirectoryLoader # for local documents
from langchain_community.document_loaders import PyPDFLoader # for local documents
from langchain_community.vectorstores import Chroma
from langchain_community import embeddings
from langchain.text_splitter import CharacterTextSplitter
import chromadb
import locale
from src.api import api_key
from src.config import config as cfg

class Retriever():
    def __init__(self, urls, document_root, embedding_model="bge-m3", language="en"):
        #super(Retriever, self).__init__()
        print(os.getcwd())
        self.urls = urls
        self.document_root = document_root
        self.embedding_model = embedding_model
        self.retriever = None
        self.deepl_translator = deepl.Translator(api_key)
        self.language = language if not cfg.languages[st.session_state['language']] else cfg.languages[st.session_state['language']]


    def _load_web_documents(self, urls):
        # Convert string of URLs to list
        with open(urls, 'r') as fh:
            urls_list = fh.readlines() #urls.split("\n")
        # This will be useful for online content
        docs = [WebBaseLoader(url).load() for url in urls_list]
        docs_list = [item for sublist in docs for item in sublist]
        return docs_list

    def _load_local_documents(self, document_root):
        docs_list = []
        files = os.listdir(document_root)
        for file in files:
            loader = PyPDFLoader(os.path.join(document_root, file))
            for page in loader.lazy_load():
                docs_list.append(page)
        return docs_list

    def load_json_files(self, directory):
        data = []
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                with open(os.path.join(directory, filename), "r", encoding="utf-8") as file:
                    data.append(json.load(file))
        return data

    def process_data_for_chromadb(self, json_data):
        documents = []
        for record_id, content in json_data.items():
            text = content.get("DIDASCALIE/TESTI ", "")  # Use the text content
            if text is None:
                print("None-content")
                text = content.get("TESTO", "")

            if int(record_id) < 200:
                text += f" Situato in: {content.get('room', '')}"
            if text and self.language != "it":
                if self.language == "en":
                    self.language = "en-us"
                text = self.deepl_translator.translate_text(text, target_lang=self.language.upper()).text

            metadata = {key: content[key] for key in content if key != "DIDASCALIE/TESTI " and key != "TESTO"}
            metadata["caption"] = text.split(".")[0]+"."
            metadata["room"] = content.get("room", "")

            for key, value in metadata.items():
                if value is None:
                    metadata[key] = "Not Available"
            documents.append({"id": record_id, "text": text, "metadata": metadata})
        return documents

    # Insert data into ChromaDB
    def insert_into_chromadb(self, collection, documents, embedding_function):
        for doc in documents:
            text = doc["text"]
            if not text.strip():
                continue  # Skip empty text
            vector = embedding_function.embed_query(text)
            collection.add(
                ids=[doc["id"]],
                metadatas=[doc["metadata"]],
                embeddings=[vector],
                documents=[text],
            )
        return collection


    def _init_retriever(self, force_reload=False):
        #if self.language == "it":
        #    cfg.chroma_db_config["path"] = f"{cfg.chroma_db_config['path']}_it"
        #else:
        cfg.chroma_db_config["path"] = f"{cfg.chroma_db_config['path']}_en"

        chromadb.api.client.SharedSystemClient.clear_system_cache()

        client = chromadb.PersistentClient(path=cfg.chroma_db_config["path"])
        collection = client.get_or_create_collection(name="rag-chroma-json")

        start = time.time()
        if os.path.exists(cfg.chroma_db_config["path"]) and os.path.isdir(cfg.chroma_db_config["path"]) and len(
                os.listdir(cfg.chroma_db_config["path"])) > 1 and not force_reload:

            print(f"Loading {cfg.chroma_db_config['path']} chroma database in {time.time() - start} seconds")
        else:

            #web_documents = self._load_web_documents(urls=self.urls)
            #local_documents = self._load_local_documents(document_root=self.document_root)
            self.document_db = self.load_json_files(cfg.local_json) #web_documents + local_documents

            #text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=1024, chunk_overlap=100)
            #doc_splits = text_splitter.split_documents(self.document_db)

            all_documents = []
            for json_data in self.document_db:
                all_documents.extend(self.process_data_for_chromadb(json_data))

            collection = self.insert_into_chromadb(collection,
                                                  all_documents,
                                                  embedding_function=embeddings.OllamaEmbeddings(model=self.embedding_model)
                                                  )
            print(f"Created {cfg.chroma_db_config['path']} chroma database in {time.time() - start} seconds")

        vectorstore = Chroma(persist_directory=cfg.chroma_db_config["path"],
                             embedding_function=embeddings.OllamaEmbeddings(model=self.embedding_model),
                             collection_name=collection.name,
                             client=client)

        '''
        vectorstore = Chroma.from_documents(
            client=client,
            documents=doc_splits,
            collection_name=collection.name,
            embedding=embeddings.OllamaEmbeddings(model=self.embedding_model)
        )
        '''


        vectorstore.as_retriever()
        self.retriever = vectorstore

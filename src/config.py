from easydict import EasyDict as edict

config = edict()
config.embedding_model="bge-m3"#"paraphrase-multilingual" #"bge-m3" #
config.urls="../web/site_pages.txt"
config.local_docs="../dummy-data/"
config.local_json="../dummy-data-json_v2/"
config.model_local="deepseek-r1" #"llama3" #deepsek-r1
config.model_trans="llama3.2:3b"
config.chroma_db_config = {
    "client": "PersistentClient",
    "timeout": 20,
    "path": f"../tmp/chroma-json-{config.model_local}-{config.embedding_model}"
}

config.languages = {
    "English": "en",
    "French": "fr",
    "Italian": "it",
    "German": "de"
}
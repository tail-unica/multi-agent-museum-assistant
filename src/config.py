from easydict import EasyDict as edict

config = edict()
config.embedding_model="paraphrase-multilingual"
config.urls="../web/site_pages.txt"
config.local_docs="../dummy-data/"
config.local_json="../dummy-data-json/"
config.model_local="llama3"
config.chroma_db_config = {
    "client": "PersistentClient",
    "timeout": 20,
    "path": "../tmp/chroma-json"
}
config.llama_parser_api = "llx-Di3KtLdfUGsLzNosaavgqGUuFKh3m8TnLljxV0tLUHoPBMpH"
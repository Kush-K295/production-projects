import chromadb
from app.core.config import DBdirectory, collection_name 

class DBmanager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DBdirectory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        

    def addBooks(self, embeddings: list, documents: list, ids: list, metadatas: list):
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
    def searchBooks(self, queryembedding: list, n_umresults: int):
        results = self.collection.query(
            query_embeddings=[queryembedding],
            n_results=n_umresults
        )
        return results
Manager = DBmanager()
from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer
from app.services.vector_store import Manager
from app.models.schemas import inputpayload, response

model = SentenceTransformer('BAAI/bge-m3')

app = FastAPI(title="KitabKosh")

@app.post("/search", response_model=response)
def semanticSearch(userSearch: inputpayload):

    try :
        userQuery = userSearch.query
        qVec = model.encode(userQuery, normalize_embeddings=True).tolist()
        result=Manager.searchBooks(queryembedding=qVec, n_results=userSearch.nresults)

        foundbooks= []
        if result and  "metadatas" in result and len(result["metadatas"])>0:
            for i in range (len(result["metadatas"][0])):
                detail =result["metadatas"][0][i]

                foundbooks.append({
                    "title": detail.get("title", ""),
                    "author": detail.get("author", ""),
                    "edition": detail.get("edition", ""),
                    "publisher": detail.get("publisher", ""),
                    "year": detail.get("year", ""),
                    "accession_nos": detail.get("accession_nos", "").split(", ")
                })
        return {"results": foundbooks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

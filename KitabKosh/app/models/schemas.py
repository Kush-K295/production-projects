from pydantic import BaseModel, Field
from typing import List, Optional

class inputpayload(BaseModel):
    query: str = Field(..., min_length=1)
    nresults : int = Field(5, ge=1, le=20)

class outputpayload(BaseModel):
    title : str
    author : str =""
    edition : str= ""
    publisher : str=""
    year : str=""
    accession_nos : List[str]

class response(BaseModel):
    results : List[outputpayload]
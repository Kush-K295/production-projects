from pydantic import BaseModel
from typing import List, Optional

class inputpayload(BaseModel):
    query : str
    num_results : int

class outputpayload(BaseModel):
    title : str
    author : str =""
    edition : str= ""
    publisher : str=""
    accession_nos : List[str]

class response(BaseModel):
    results : List[outputpayload]
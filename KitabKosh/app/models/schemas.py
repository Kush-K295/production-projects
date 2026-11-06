from pydantic import BaseModel
from typing import List, Optional

class inputpayload(BaseModel):
    query : str
    nresults : int

class outputpayload(BaseModel):
    title : str
    author : str =""
    edition : str= ""
    publisher : str=""
    year : str=""
    accession_nos : List[str]

class response(BaseModel):
    results : List[outputpayload]
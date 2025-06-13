from typing import Union
from functools import lru_cache
from fastapi import FastAPI
from config import Settings

app = FastAPI()


@lru_cache
def get_settings():
    return Settings()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
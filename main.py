from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

# from .fade_in_video import fade_in_video

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

class Variables(BaseModel):
    variables: Dict[str, Any]

@app.post("/fade-in-video")
def read_item(body: Variables):
    # output_file = fade_in_video(input_video_path, "bakwas", fade_duration)
    # Upload to S3 and return URL.
    return {"video": "THIS IS THE EC@ TALKING"}

@app.post("/compress")
def read_item(body: Variables):
    # output_file = fade_in_video(input_video_path, "bakwas", fade_duration)
    # Upload to S3 and return URL.
    return {"video": "THIS IS THE COMPRESS FUNCTION"}
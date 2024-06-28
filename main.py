from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

# from .fade_in_video import fade_in_video

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}



class FadeInBody(BaseModel):
    input_video_path: str
    fade_duration: float

@app.post("/fade-in-video")
def read_item(FadeInBody):
    # output_file = fade_in_video(input_video_path, "bakwas", fade_duration)
    # Upload to S3 and return URL.
    return {"video": "THIS IS THE EC@ TALKING"}
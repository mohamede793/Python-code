from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

from resize_video import resize_video
from trim_video import trim_video


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

class Variables(BaseModel):
    variables: Dict[str, Any]

@app.post("/trim_video")
def trim_video_endpoint():
    # output_file = trim_video(body.variables)
    return "THIS IS THE trim video"

@app.post("/add_video")
def add_video_endpoint(body: Variables):
    # output_file = add_video(body.variables)
    return "THIS IS THE add video"

@app.post("/add_audio")
def add_audio_endpoint(body: Variables):
    # output_file = add_audio(body.variables)
    return "THIS IS THE add audio"

@app.post("/fade_in_video")
def fade_in_video_endpoint(body: Variables):
    # output_file = fade_in_video(body.variables)
    return "THIS IS THE fade in video"

@app.post("/fade_out_video")
def fade_out_video_endpoint(body: Variables):
    # output_file = fade_out_video(body.variables)
    return "THIS IS THE fade out video"

@app.post("/fade_in_audio")
def fade_in_audio_endpoint(body: Variables):
    # output_file = fade_in_audio(body.variables)
    return "THIS IS THE fade in audio"

@app.post("/fade_out_audio")
def fade_out_audio_endpoint(body: Variables):
    # output_file = fade_out_audio(body.variables)
    return "THIS IS THE fade out audio"

@app.post("/change_audio_volume")
def change_audio_volume_endpoint(body: Variables):
    # output_file = change_audio_volume(body.variables)
    return "THIS IS THE change audio volume"

@app.post("/remove_audio")
def remove_audio_endpoint(body: Variables):
    # output_file = remove_audio(body.variables)
    return "THIS IS THE remove audio"

@app.post("/other_edit")
def other_edit_endpoint(body: Variables):
    # output_file = other_edit(body.variables)
    return "THIS IS THE other edit"

@app.post("/help")
def help_endpoint(body: Variables):
    # output_file = help(body.variables)
    return "THIS IS THE help"
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
def read_item(body: Variables):
    return "HELLLOOO"
    output = trim_video(body.variables)
    return output

# @app.post("/add_video")
# def read_item(body: Variables):
#     # output_file = add_video(body.variables)
#     return "THIS IS THE add video"

# @app.post("/add_audio")
# def read_item(body: Variables):
#     # output_file = add_audio(body.variables)
#     return "THIS IS THE add audio"

# @app.post("/fade_in_video")
# def read_item(body: Variables):
#     # output_file = fade_in_video(body.variables)
#     return "THIS IS THE fade in video"

# @app.post("/fade_out_video")
# def read_item(body: Variables):
#     # output_file = fade_out_video(body.variables)
#     return "THIS IS THE fade out video"

# @app.post("/fade_in_audio")
# def read_item(body: Variables):
#     # output_file = fade_in_audio(body.variables)
#     return "THIS IS THE fade in audio"

# @app.post("/fade_out_audio")
# def read_item(body: Variables):
#     # output_file = fade_out_audio(body.variables)
#     return "THIS IS THE fade out audio"

# @app.post("/change_audio_volume")
# def read_item(body: Variables):
#     # output_file = change_audio_volume(body.variables)
#     return "THIS IS THE change audio volume"

# @app.post("/remove_audio")
# def read_item(body: Variables):
#     # output_file = remove_audio(body.variables)
#     return "THIS IS THE remove audio"

# @app.post("/other_edit")
# def read_item(body: Variables):
#     # output_file = other_edit(body.variables)
#     return "THIS IS THE other edit"

# @app.post("/help")
# def read_item(body: Variables):
#     # output_file = help(body.variables)
#     return "THIS IS THE help"
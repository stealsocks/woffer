from fastapi import FastAPI, status, File, Form, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse
import random
import os
from typing import List, Union
from fastapi.responses import HTMLResponse, FileResponse
import subprocess
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
import time

# Go to the path "/docs" to play with the requests!
app = FastAPI()

UTF_map = {
    "latin_basic": "U+0000-007F",
    "latin_1": "U+0080-00FF",
    "punctuation": "U+2000-206F"
}


@app.get("/hello")
def hello_world():
    return "Hello, World!"


@app.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(
    description="Multiple files as UploadFile"), ):
    return {"filenames": [file.filename for file in files]}


@app.post("/convert/")
async def create_upload_file(
        background_tasks: BackgroundTasks,
        file: Union[UploadFile, None] = None,
        # token: str = Form(),
        latin: bool = Form(False),
        latin_1: bool = Form(False),
        punctuation: bool = Form(False)):

    if not file:
          response = RedirectResponse(url="https://woffer.joodaloop.com/error", status_code=status.HTTP_303_SEE_OTHER)
          response.headers["Location"] = "https://woffer.joodaloop.com/error"
          return response
    
    else:
        f = await file.read()
        fname = file.filename.split(".")[0]
      
        if len(f) == 0:
            response = RedirectResponse(url="https://woffer.joodaloop.com/error", status_code=status.HTTP_303_SEE_OTHER)
            response.headers["Location"] = "https://woffer.joodaloop.com/error"
            return response

        elif(file.filename.split(".")[-1] != "ttf"):
            response = RedirectResponse(url="https://woffer.joodaloop.com/error", status_code=status.HTTP_303_SEE_OTHER)
            response.headers["Location"] = "https://woffer.joodaloop.com/error"
            return response
          
        else:
            file.file.seek(0)    
            UTF_range = ''''''
            utfs = []
            print(latin, latin_1, punctuation)
            if (latin == True):
              utfs.append(UTF_map["latin_basic"])
            if (latin_1 == True):
              utfs.append(UTF_map["latin_1"])
            if (punctuation == True):
              utfs.append(UTF_map["punctuation"])
            UTF_range = ", ".join(utfs).strip()
            if len(UTF_range) == 0:
              UTF_range = "*"
            print(UTF_range)
            with open(file.filename, "wb+") as file_object:
                file_object.write(file.file.read())
    
            res = await subset('{}'.format(fname), UTF_range)
          
            background_tasks.add_task(delete_files, res)
            return FileResponse(path="{}.woff2".format(res),
                                media_type="font/woff2",
                                filename="{}.woff2".format(res))


def delete_files(fname):
    os.remove(fname + ".ttf")
    os.remove(fname + ".woff2")


@app.get("/")
async def main():
    content = """
<body>
<form action="/convert/" enctype="multipart/form-data" method="post">

<label for="checkbox-1">Latin Basic:</label>
<input type="checkbox" id="checkbox-1" name="latin"><br>

<label for="checkbox-2">Latin-1 Extended:</label>
<input type="checkbox" id="checkbox-2" name="latin_1"><br>

<label for="checkbox-3">Puntuation:</label>
<input type="checkbox" id="checkbox-3" name="punctuation"><br>

File: <input name="file" type="file">
<input type="submit">
</form>

</body>
    """
    return HTMLResponse("<a href='https/woffer.joodaloop.com'> Go to app ---></a>")


def compress(font_name):
    cmd = '''ls
            cd woff2
            ls
            ./woff2_compress ../{}.ttf'''.format(font_name)

    subprocess.Popen('cd woff2;{};'.format(cmd), shell=True)


async def subset(font_name, utf_range):
    cmd = '''pyftsubset {}.ttf --unicodes='{}' --layout-features='*' --flavor="woff2" --output-file="{}.woff2"'''.format(
        font_name, utf_range, font_name)
    # s1 = utf_range
    # s2 = "U+0000-007F"
    # for i in range(len(s1)):
    #     print(ord(s1[i]))
    #     print(ord(s2[i]))
  

    process = subprocess.Popen('{}; ls'.format(cmd), shell=True)
    out, err = process.communicate()
    errcode = process.returncode
    return font_name

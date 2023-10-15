from fastapi import FastAPI, UploadFile, HTTPException, Form
from starlette.responses import FileResponse
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
import os
from fastapi.middleware.cors import CORSMiddleware
from zipfile import ZipFile
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_fonts"
CONVERTED_DIR = "converted_fonts"

# Ensure directories exist
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
if not os.path.exists(CONVERTED_DIR):
    os.makedirs(CONVERTED_DIR)

def convert_to_woff2(input_file_path, output_file_path, unicodes=None):
    font = TTFont(input_file_path)

    if unicodes:
        options = Options()
        options.flavor = 'woff2'
        options.unicodes = unicodes
        subsetter = Subsetter(options=options)
        subsetter.populate(unicodes=unicodes)
        subsetter.subset(font)
    else:
        font.flavor = 'woff2'

    font.save(output_file_path)

@app.post("/upload", response_class=FileResponse)
async def upload_font(
    files: List[UploadFile] = Form(...),
    latin: bool = Form(False),
    latin_1: bool = Form(False),
    punctuation: bool = Form(False)
  ):
    if not isinstance(files, list):
        files = [files]
    
    unicodes = []

    if latin:
        unicodes.extend(range(0x0000, 0x007F + 1))
    if latin_1:
        unicodes.extend(range(0x0080, 0x00FF + 1))
    if punctuation:
        unicodes.extend(range(0x2000, 0x206F + 1))

    zip_filename = "converted_fonts.zip"
    zip_path = os.path.join(CONVERTED_DIR, zip_filename)

    with ZipFile(zip_path, 'w') as zipf:
        for file in files:
            # Ensure the file has a font extension
            ext = file.filename.split('.').pop().lower()
            if ext not in ['ttf', 'otf', 'woff', 'woff2']:
                raise HTTPException(status_code=400, detail=f"Invalid font file format for {file.filename}")

            file_path = os.path.join(UPLOAD_DIR, file.filename)

            # Save the uploaded font file
            with open(file_path, "wb") as buffer:
                buffer.write(file.file.read())

            # Convert to woff2
            output_filename = f"{os.path.splitext(file.filename)[0]}.woff2"
            output_path = os.path.join(CONVERTED_DIR, output_filename)
            convert_to_woff2(file_path, output_path, unicodes=unicodes)

            zipf.write(output_path, output_filename)

            # Cleanup: Delete both the uploaded and converted files
            os.remove(file_path)
            os.remove(output_path)

    return zip_path

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

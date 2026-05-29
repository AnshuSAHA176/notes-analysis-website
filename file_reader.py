from sys import platform

from PyPDF2 import PdfReader
import os 
from docx import Document
from PIL import Image
import pytesseract



class File_Reader():
    def __init__(self,file_name):
        self.file_name=file_name
        self.file_path=f"static/files/{file_name}"
        
    def pdf_reader(self):
        reader = PdfReader(self.file_path)

        parts = []

        def visitor_body(text, cm, tm, fontDict, fontSize):

            y = tm[5]

            if 50 < y < 720:
                parts.append(text)

        for page in reader.pages:

            page.extract_text(visitor_text=visitor_body)

        text_body = "".join(parts)

        return (text_body)


    def docx_reader(self):
        doc=Document(self.file_path)
        texts=[text.text for text in doc.paragraphs]
        format_text=".\n".join(texts)
        return (format_text)


    def screenshot_photo_reader(self):

            import platform

            if platform.system() == "Darwin":  # MacOS
                 pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

            image = Image.open(self.file_path)

            text = pytesseract.image_to_string(image)

            return (text)


from docx import Document
import nltk
from nltk.tokenize import word_tokenize
from globals import globalvars


def iterate_paragraphs(doc):
    in_data = False
    data = []
    for para in doc.paragraphs:
        if para.text == 'data-start':
            in_data = True
        elif para.text == 'data-end':
            in_data = False
        elif in_data:
            print(para.text)
            if para.text:
                # Make sure text is not over max tokens
                if len(nltk.word_tokenize(para.text)) > globalvars.MAX_TOKENS:
                    para.text = para.text[0:globalvars.MAX_TOKENS]
                data.append(para.text)
    return data


def get_data(docx_file):
    doc = Document(docx_file)
    return iterate_paragraphs(doc)

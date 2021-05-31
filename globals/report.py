import os
from contextlib import contextmanager,redirect_stderr,redirect_stdout
from os import devnull, name
import sys
import logging
import psutil
from sklearn.feature_extraction import text
from topic_modeling import stopwords
from . import globalvars
import sentop_config as config
import nltk
from nltk.tokenize import word_tokenize
import string
from openpyxl import Workbook
from openpyxl.styles import Color, PatternFill, Font, Border
from openpyxl.styles import colors
from openpyxl.cell import Cell



html_start = """<html>\n 
             <head></head>\n
             <body>
             """
html_end = """</body>
             </html>
             """

class SentopLog():
    def __init__(self):
        self.id = html_start

    def append(self, text):
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + text + "\n"
        print(text)

    def clear(self):
        globalvars.SENTOP_LOG = html_start

    def write(self, id, output_dir_path):
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html_end + "\n"
        log_out = output_dir_path + "\\" + id + "_log.html"
        f= open(log_out,"w+")
        f.write(globalvars.SENTOP_LOG)
        f.close

    

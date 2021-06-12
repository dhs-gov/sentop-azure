from datetime import datetime
from dateutil import tz
from . import globalvars



html_start = """<html>\n 
             <head>
             <style>
                body {line-height: 140%;}
                h1 {font-size: 24px; font-weight: bold; color: #235668;}
                h2 {font-size: 20px; font-weight: bold; color: #5498b0;}
                h3 {font-size: 16px; font-weight: bold; color: brown;}
                pre {font-size: 14px;}
                p    {color: red;}
                b {color: #525252;}
                hr {color: silver}
</style>
             
             </head>\n
             <body style=\"font-family: arial; \">\n
             """
html_end = """</body>\n
             </html>
             """

class SentopLog():
    def __init__(self):
        self.id = html_start
        self.log_level = 0

    def set_level(self, level):
        if level == 'DEBUG':
            self.log_level = 0
        elif level == 'INFO':
            self.log_level = 1
        elif level == 'WARNING':
            self.log_level = 2
        elif level == 'ERROR':
            self.log_level = 3
        else:
            print("Unknown logging level. Setting to INFO.")
            self.log_level = 1
        print(f"Logging level: {self.log_level}")

    def h1(self, text):
        html = f"<h1>{text}</h1>"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
        print(text)

    def h2(self, text):
        html = f"<h2>{text}</h2>"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
        print(text)

    def h3(self, text):
        html = f"<h3>{text}</h3>"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
        print(text)

    def p(self, text):
        html = f"{text}"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
        print(text)

    def other(self, text):
        html = f"{text}"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
        #print(text)

    def keyval(self, text):
        keyval_list = text.split('|')
        if not keyval_list:
            self.error("Did not find '|' char in keyval parameter'")
            return

        key = keyval_list[0]
        val = keyval_list[1]
        if not val:
            val = ""
        html = f"<b>&#8226; {key}:</b> {val}<br>"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
        print(f"{key}: {val}")

    '''
    def append(self, text):
        html = f"{text}<br>"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
        print(text)
    '''

    def write_tag(self, text, html_tag):
        if html_tag == 'h1' or html_tag == 'H1':
            self.h1(text)
        elif html_tag == 'h2' or html_tag == 'H2':
            self.h2(text)
        elif html_tag == 'h3' or html_tag == 'H3':
            self.h3(text)
        elif html_tag == 'p' or html_tag == 'P':
            self.p(text)
        elif html_tag == 'other':
            self.other(text)
        elif html_tag == 'keyval':
            self.keyval(text)

    def debug(self, text, html_tag):
        if self.log_level == 0:
            self.write_tag(text, html_tag)

    def info(self, text, html_tag):
        if self.log_level <= 1:
            self.write_tag(text, html_tag)

    def warn(self, text):
        if self.log_level <= 2:
            html = f"<div style=\"font-weight: bold; color: #e97e16; \">&#8226; WARNING: {text} </div>"
            globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
            print(text)

    def error(self, text):
        if self.log_level <= 3:
            html = f"<div style=\"font-weight: bold; color: red; \">&#8226; ERROR: {text} </div>"
            globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
            print(text)

    def reset(self):
        print(">>>>>>>>>>>>>>>>>> S T A R T >>>>>>>>>>>>>>>>")
        globalvars.SENTOP_LOG = html_start
        html = "<br><br><div style=\"line-height: 110%; text-align: center; font-size: 30px; font-weight: bold;\">SENTOP</div>\n"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
        html = "<div style=\"line-height: 160%; text-align: center; font-size: 18px;\"><a href=\"https://github.com/dhs-gov/sentop\" target=\"_blank\">github.com/dhs-gov/sentop</a></div>\n"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/New_York')
        utc = datetime.utcnow()
        utc = utc.replace(tzinfo=from_zone)
        central = utc.astimezone(to_zone)
        html = f"<div style=\"text-align: center; font-size: 16px;\">{central.strftime('%B %d %Y - %H:%M:%S')} EST</div><br>\n"
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html + "\n"

    def write(self, id, output_dir_path):
        globalvars.SENTOP_LOG = globalvars.SENTOP_LOG + html_end + "\n"
        log_out = output_dir_path + "\\" + id + "_log.html"
        f= open(log_out,"w+")
        f.write(globalvars.SENTOP_LOG)
        f.close

    

    

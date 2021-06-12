'''
This model classifies offensive text using the following labels:
not_offensive
offensive
'''

from globals import globalutils
from globals import sentop_log

model_name = "cardiffnlp/twitter-roberta-base-offensive"


def calc_sentiment(confidence_score):
    largest_label = 'LABEL_0'
    largest_score = 0.0

    for label in confidence_score.labels:
        #print("cf: ", label)
        if label.score > largest_score:
            largest_label = str(label)
            largest_score = label.score

    #print("largest_label: ", largest_label)
    if "LABEL_0" in largest_label:
        return "not_offensive"
    elif "LABEL_1" in largest_label:
        return "offensive"
    else:
        print("WARNING: unknown sentiment")
        return "not_offensive"
        

def get_sentiment(classifier, text):

    globalutils.block_logging()
    with globalutils.suppress_stdout_stderr():

        confidence_scores = classifier.tag_text(
            text=text,
            #"nlptown/bert-base-multilingual-uncased-sentiment"
            #"cardiffnlp/twitter-roberta-base-emotion"
            model_name_or_path=model_name,
            mini_batch_size=1
        )
    globalutils.enable_logging()

    # This should only loop once
    for confidence_score in confidence_scores:
        return calc_sentiment(confidence_score)

def print_totals(sentiments):
    sentlog = sentop_log.SentopLog()
    notoffensive = 0
    offensive = 0
    for sentiment in sentiments:
        if sentiment == 'not_offensive':
            notoffensive = notoffensive + 1
        elif sentiment == 'offensive':
            offensive = offensive + 1

    sentlog.append(f"<pre>")
    sentlog.append(f"- Not Offensive: {notoffensive}")
    sentlog.append(f"- Offesnive: {offensive}")
    sentlog.append(f"</pre>")


def assess(classifier, docs):
    sentlog = sentop_log.SentopLog()
    sentlog.append(f"<h2>Offensive</h2>\n")
    sentlog.append(f"<b>Model: </b> <a href=\"https://huggingface.co/{model_name}\" target=\"_blank\">{model_name}</a><br>")
    sentiments = []
    i = 0
    for doc in docs:
        #print("doc: ", doc)
        sentiment = get_sentiment(classifier, doc)
        
        if sentiment:
            sentiments.append(sentiment)
        else:
            print("Error: sentiment is NoneType")

        #if i % 100 == 0:
        #    print("Processing 5-class: ", i)
        i = i + 1
    print_totals(sentiments)
    return globalutils.Sentiments("offensive1", f"Offensive ({model_name})", model_name, "offensive", sentiments)


'''
This model classifies sentiment polarity using the following labels:
1 star
2 stars
3 stars
4 stars
5 stars
'''

from globals import globalutils
from globals import sentop_log

model_name = "nlptown/bert-base-multilingual-uncased-sentiment"


def calc_sentiment(confidence_score):
    largest_label = "LABEL_0"
    largest_score = 0.0

    for label in confidence_score.labels:
        #print("5STAR LABEL: ", label)
        if label.score > largest_score:
            largest_label = str(label)
            largest_score = label.score

    if "1 star" in largest_label:
        return "1_star"
    elif "2 stars" in largest_label:
        return "2_stars"
    elif "3 stars" in largest_label:
        return "3_stars"
    elif "4 stars" in largest_label:
        return "4_stars"
    elif "5 stars" in largest_label:
        return "5_stars"
    else:
        print("Error: sentiment is NoneType")
        return "3_stars"
        

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
    star1 = 0
    star2 = 0
    star3 = 0
    star4 = 0
    star5 = 0
    for sentiment in sentiments:
        if sentiment == '1_star':
            star1 = star1 + 1
        elif sentiment == '2_stars':
            star2 = star2 + 1
        elif sentiment == '3_stars':
            star3 = star3 + 1
        elif sentiment == '4_stars':
            star4 = star4 + 1
        elif sentiment == '5_stars':
            star5 = star5 + 1
    sentlog.append(f"<pre>")
    sentlog.append(f"- 1 Star: {star1}")
    sentlog.append(f"- 2 Stars: {star2}")
    sentlog.append(f"- 3 Stars: {star3}")
    sentlog.append(f"- 4 Stars: {star4}")
    sentlog.append(f"- 5 Stars: {star5}")
    sentlog.append(f"</pre>")


def assess(classifier, docs):
    sentlog = sentop_log.SentopLog()
    sentlog.append(f"<h2>5-Class Polarity</h2>\n")
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
    return globalutils.Sentiments("class5", f"5-Class ({model_name})", model_name, "polarity", sentiments)


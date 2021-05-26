from globals import globalutils


def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d + '0' * n)[:n]])


class Sentiment:
    def __init__(self, sentiment, joy, optimism, anger, sadness):
        self.sentiment = sentiment
        self.joy = float(truncate(joy, 3))
        self.optimism = float(truncate(optimism, 3))
        self.anger = float(truncate(anger, 3))
        self.sadness = float(truncate(sadness, 3))

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
        return "anger"
    elif "LABEL_1" in largest_label:
        return "joy"
    elif "LABEL_2" in largest_label:
        return "optimism"
    elif "LABEL_3" in largest_label:
        return "sadness"   
    else:
        print("WARNING: unknown sentiment")
        return "optimism"
        

def get_sentiment(classifier, text):

    globalutils.block_logging()
    with globalutils.suppress_stdout_stderr():

        confidence_scores = classifier.tag_text(
            text=text,
            #"nlptown/bert-base-multilingual-uncased-sentiment"
            #"cardiffnlp/twitter-roberta-base-emotion"
            model_name_or_path="cardiffnlp/twitter-roberta-base-emotion",
            mini_batch_size=1
        )
    globalutils.enable_logging()

    # This should only loop once
    for confidence_score in confidence_scores:

        sentiment = Sentiment(
            calc_sentiment(confidence_score),
            confidence_score.labels[0].score,
            confidence_score.labels[1].score,
            confidence_score.labels[2].score,
            confidence_score.labels[3].score
            )
        return sentiment


def assess(classifier, docs):
    sentlog = globalutils.SentopLog()
    sentlog.append("----------------------------------------------------------")
    sentlog.append("Assessing emotion sentiment. Please wait...")
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
        #    print("Processing 3-class: ", i)
        i = i + 1

    return sentiments

from globals import globalutils


def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d + '0' * n)[:n]])


class Sentiment:
    def __init__(self, sentiment, vneg, neg, neutral, pos, vpos):
        self.sentiment = sentiment
        self.very_negative = float(truncate(vneg, 3))
        self.negative = float(truncate(neg, 3))
        self.neutral = float(truncate(neutral, 3))
        self.positive = float(truncate(pos, 3))
        self.very_positive = float(truncate(vpos, 3))


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
            model_name_or_path="nlptown/bert-base-multilingual-uncased-sentiment",
            mini_batch_size=1,
        )
    globalutils.enable_logging()

    # This should only loop once
    for confidence_score in confidence_scores:
        sentiment = Sentiment(
            calc_sentiment(confidence_score),
            confidence_score.labels[0].score,
            confidence_score.labels[1].score,
            confidence_score.labels[2].score,
            confidence_score.labels[3].score,
            confidence_score.labels[4].score
        )
        return sentiment


def assess(classifier, docs):
    sentlog = globalutils.SentopLog()
    sentlog.append("----------------------------------------------------------")
    sentlog.append("Assessing 5-star sentiment. Please wait...")
    sentiments = []
    i = 0
    
    for doc in docs:
        #print("doc: ", doc)
        sentiment = get_sentiment(classifier, doc)

        if sentiment:
            sentiments.append(sentiment)
        else:
            print("Error: sentiment is NoneType")
        #if i % 10 == 0:
        #    print("Processing 5-star: ", i)
        i = i + 1

    return sentiments

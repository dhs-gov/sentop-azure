from globals import globalutils

model_name = "cardiffnlp/twitter-roberta-base-emotion"


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
            model_name_or_path=model_name,
            mini_batch_size=1
        )
    globalutils.enable_logging()

    # This should only loop once
    for confidence_score in confidence_scores:
        return calc_sentiment(confidence_score)


def assess(classifier, docs):
    sentlog = globalutils.SentopLog()
    sentlog.append("----------------------------------------------------------")
    sentlog.append(f"Assessing emotion ({model_name}). Please wait...")
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

    return globalutils.Sentiments("emotion1", f"Emotion ({model_name})", model_name, "emotion", sentiments)


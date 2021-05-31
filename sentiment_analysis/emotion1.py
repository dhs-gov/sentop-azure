'''
This model classifies emotion using the following labels:
anger
joy
optimism
sadness 
'''

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

def print_totals(sentiments):
    sentlog = globalutils.SentopLog()
    joy = 0
    anger = 0
    optimism = 0
    sadness = 0

    for sentiment in sentiments:
        if sentiment == 'joy':
            joy = joy + 1
        elif sentiment == 'anger':
            anger = anger + 1
        elif sentiment == 'optimism':
            optimism = optimism + 1
        elif sentiment == 'sadness':
            sadness = sadness + 1

    sentlog.append(f"<pre>")
    sentlog.append(f"- Joy: {joy}")
    sentlog.append(f"- Anger: {anger}")
    sentlog.append(f"- Optimism: {optimism}")
    sentlog.append(f"- Sadness: {sadness}")
    sentlog.append(f"</pre>")


def assess(classifier, docs):
    sentlog = globalutils.SentopLog()
    sentlog.append(f"<h2>Emotion 1</h2>\n")
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
    return globalutils.Sentiments("emotion1", f"Emotion1 ({model_name})", model_name, "emotion", sentiments)


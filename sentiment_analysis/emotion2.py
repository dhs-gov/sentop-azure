'''
This model classifies emotion using the following labels:
admiration
amusement 
anger
annoyance 
approval 
caring
confusion 
curiosity 
desire
disappointment
disapproval
disgust
embarrassment   
excitement
fear
gratitude 
grief
joy
love
nervousness
neutral     
optimism  
pride
realization
relief
remorse
sadness
surprise  
'''

from globals import globalutils


model_name = "monologg/bert-base-cased-goemotions-original"


def calc_sentiment(confidence_score):
    largest_label = 'LABEL_0' 
    largest_score = 0.0

    for label in confidence_score.labels:
        #print("Emotion2 INTENT LABEL: ", label) 
        if label.score > largest_score:
            largest_label = str(label)
            largest_score = label.score
            #print(f"Largest score: {largest_score}")

    labels = largest_label.split()
    #print(f"largest label: {labels[0]}")
    return labels[0]
        

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
        #print(f"INTENT: {confidence_score.to_plain_string()}")

        return calc_sentiment(confidence_score)


def assess(classifier, docs):
    sentlog = globalutils.SentopLog()
    sentlog.append("----------------------------------------------------------")
    sentlog.append(f"Assessing emotion2 ({model_name}). Please wait...")
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

    return globalutils.Sentiments("emotion2", f"Emotion2 ({model_name})", model_name, "emotion", sentiments)

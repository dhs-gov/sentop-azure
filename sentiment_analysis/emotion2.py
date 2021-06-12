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
from globals import sentop_log


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

def print_totals(sentiments):
    sentlog = sentop_log.SentopLog()
    admiration = 0
    amusement  = 0
    anger = 0
    annoyance  = 0
    approval  = 0
    caring = 0
    confusion  = 0
    curiosity  = 0
    desire = 0
    disappointment = 0
    disapproval = 0
    disgust = 0
    embarrassment    = 0
    excitement = 0
    fear = 0
    gratitude  = 0
    grief = 0
    joy = 0
    love = 0
    nervousness = 0
    neutral     = 0 
    optimism   = 0
    pride = 0
    realization = 0
    relief = 0
    remorse = 0
    sadness = 0
    surprise  = 0

    for sentiment in sentiments:
        if sentiment == 'admiration':
            admiration = admiration + 1
        elif sentiment == 'amusement':
            amusement = amusement + 1
        elif sentiment == 'anger':
            anger = anger + 1
        elif sentiment == 'annoyance':
            annoyance = annoyance + 1
        if sentiment == 'approval':
            approval = approval + 1
        elif sentiment == 'caring':
            caring = caring + 1
        elif sentiment == 'confusion':
            confusion = confusion + 1
        elif sentiment == 'curiosity':
            curiosity = curiosity + 1
        if sentiment == 'desire':
            desire = desire + 1
        elif sentiment == 'disappointment':
            disappointment = disappointment + 1
        elif sentiment == 'disapproval':
            disapproval = disapproval + 1
        elif sentiment == 'disgust':
            disgust = disgust + 1
        if sentiment == 'embarrassment':
            embarrassment = embarrassment + 1
        elif sentiment == 'excitement':
            excitement = excitement + 1
        elif sentiment == 'fear':
            fear = fear + 1      
        elif sentiment == 'gratitude':
            gratitude = gratitude + 1
        elif sentiment == 'grief':
            grief = grief + 1
        if sentiment == 'joy':
            joy = joy + 1
        elif sentiment == 'love':
            love = love + 1
        elif sentiment == 'nervousness':
            nervousness = nervousness + 1
        elif sentiment == 'neutral':
            neutral = neutral + 1
        elif sentiment == 'optimism':
            optimism = optimism + 1    
        elif sentiment == 'pride':
            pride = pride + 1
        elif sentiment == 'realization':
            realization = realization + 1
        elif sentiment == 'relief':
            relief = relief + 1
        elif sentiment == 'remorse':
            remorse = remorse + 1
        elif sentiment == 'sadness':
            sadness = sadness + 1
        elif sentiment == 'surprise':
            surprise = surprise + 1

    sentlog.append(f"<pre>")
    sentlog.append(f"- Admiration: {admiration}")
    sentlog.append(f"- Amusement: {amusement}")
    sentlog.append(f"- Anger: {anger}")
    sentlog.append(f"- Annoyance: {annoyance}")
    sentlog.append(f"- Approval: {approval}")
    sentlog.append(f"- Caring: {caring}")
    sentlog.append(f"- Confusion: {confusion}")
    sentlog.append(f"- Curiosity: {curiosity}")
    sentlog.append(f"- Desire: {desire}")
    sentlog.append(f"- Dissapointment: {disappointment}")
    sentlog.append(f"- Disapproval: {disapproval}")
    sentlog.append(f"- Embarrassment: {embarrassment}")
    sentlog.append(f"- Excitement: {excitement}")
    sentlog.append(f"- Fear: {fear}")
    sentlog.append(f"- Gratitude: {gratitude}")
    sentlog.append(f"- Grief: {grief}")
    sentlog.append(f"- Joy: {joy}")
    sentlog.append(f"- Love: {love}")
    sentlog.append(f"- Nervousness: {nervousness}")
    sentlog.append(f"- Neutral: {neutral}")
    sentlog.append(f"- Optimism: {optimism}")
    sentlog.append(f"- Pride: {pride}")
    sentlog.append(f"- Realization: {realization}")
    sentlog.append(f"- Relief: {relief}")
    sentlog.append(f"- Remorse: {remorse}")
    sentlog.append(f"- Sadness: {sadness}")
    sentlog.append(f"- Surprise: {surprise}")
    sentlog.append(f"</pre>")


def assess(classifier, docs):
    sentlog = sentop_log.SentopLog()
    sentlog.append(f"<h2>Emotion 2</h2>\n")
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
        #    print("Processing 3-class: ", i)
        i = i + 1
    print_totals(sentiments)
    return globalutils.Sentiments("emotion2", f"Emotion2 ({model_name})", model_name, "emotion", sentiments)

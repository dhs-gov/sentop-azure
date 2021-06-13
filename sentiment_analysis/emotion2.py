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

    sentlog.info(f"<pre>", html_tag='other')
    sentlog.info(f"- Admiration: {admiration}", html_tag='p')
    sentlog.info(f"- Amusement: {amusement}", html_tag='p')
    sentlog.info(f"- Anger: {anger}", html_tag='p')
    sentlog.info(f"- Annoyance: {annoyance}", html_tag='p')
    sentlog.info(f"- Approval: {approval}", html_tag='p')
    sentlog.info(f"- Caring: {caring}", html_tag='p')
    sentlog.info(f"- Confusion: {confusion}", html_tag='p')
    sentlog.info(f"- Curiosity: {curiosity}", html_tag='p')
    sentlog.info(f"- Desire: {desire}", html_tag='p')
    sentlog.info(f"- Dissapointment: {disappointment}", html_tag='p')
    sentlog.info(f"- Disapproval: {disapproval}", html_tag='p')
    sentlog.info(f"- Embarrassment: {embarrassment}", html_tag='p')
    sentlog.info(f"- Excitement: {excitement}", html_tag='p')
    sentlog.info(f"- Fear: {fear}", html_tag='p')
    sentlog.info(f"- Gratitude: {gratitude}", html_tag='p')
    sentlog.info(f"- Grief: {grief}", html_tag='p')
    sentlog.info(f"- Joy: {joy}", html_tag='p')
    sentlog.info(f"- Love: {love}", html_tag='p')
    sentlog.info(f"- Nervousness: {nervousness}", html_tag='p')
    sentlog.info(f"- Neutral: {neutral}", html_tag='p')
    sentlog.info(f"- Optimism: {optimism}", html_tag='p')
    sentlog.info(f"- Pride: {pride}", html_tag='p')
    sentlog.info(f"- Realization: {realization}", html_tag='p')
    sentlog.info(f"- Relief: {relief}", html_tag='p')
    sentlog.info(f"- Remorse: {remorse}", html_tag='p')
    sentlog.info(f"- Sadness: {sadness}", html_tag='p')
    sentlog.info(f"- Surprise: {surprise}", html_tag='p')
    sentlog.info(f"</pre>", html_tag='other')


def assess(classifier, docs):
    sentlog = sentop_log.SentopLog()
    sentlog.info(f"Emotion 2", html_tag='h2')
    sentlog.info(f"Model|<a href=\"https://huggingface.co/{model_name}\" target=\"_blank\">{model_name}</a>", html_tag='keyval')
    sentiments = []
    for doc in docs:
        #print("doc: ", doc)
        sentiment = get_sentiment(classifier, doc)
        if sentiment:
            sentiments.append(sentiment)
        else:
            sentlog.warn("Sentiment is None type.")
    print_totals(sentiments)
    return globalutils.Sentiments("emotion2", f"Emotion2 ({model_name})", model_name, "emotion", sentiments)

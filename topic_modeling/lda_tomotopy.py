import tomotopy as tp
from globals import globalutils
# NLTK Lemmatizer does not work well
import re
#from transformers import AutoTokenizer, AutoModelForTokenClassification, TokenClassificationPipeline
from . import config_topic_mod as config     
from globals import globalutils
from data_util import data_cleaner

class KeyWeight:
    def __init__(self, key, weight):
        self.key = key
        self.weight = weight


'''
class Topic:
    def __init__(self, topic_num, words, weights):
        self.topic_num = topic_num
        self.words = words
        self.weights = weights
'''

def get_coherence(data_preprocessed, k):
    
    #print("Getting coherence for size ", k)
    mdl = tp.LDAModel(seed=1, min_df=5, rm_top=0, k=k)  

    for row in data_preprocessed:
        if not row:
            # A row may be None after preprocessing (e.g., if all words are stop words)
            print(f"GOT BLANK ROW!! QUIT! -- '{row}'")
            row = "NA"
        try:
            mdl.add_doc(row.strip().split())
        except Exception as e:
            print("except row: ", row)
            globalutils.show_stack_trace(str(e))

    mdl.burn_in = 100
    mdl.train(0)

    for i in range(0, 100, 10):
        mdl.train(10)
        #print('Iteration: {}\tLog-likelihood: {}'.format(i, mdl.ll_per_word))

    #print("dist: ", mdl.get_topic_word_dist)
    '''
    for i in range(mdl.k):
        #print('Top words of topic #{}'.format(k))
        print(mdl.get_topic_words(i, top_n=10))

    mdl.summary()


    for j in range(mdl.k):
        print('Topic #{}'.format(j))
        for word, prob in mdl.get_topic_words(j):
            print('\t', word, prob, sep='\t')
    '''

    # calculate coherence using preset
    #coherence_score = -999999.99
    # We use only C_v based on http://svn.aksw.org/papers/2015/WSDM_Topic_Evaluation/public.pdf
    # for preset in ('u_mass', 'c_uci', 'c_npmi', 'c_v'):
    preset = 'c_v'
    coh = tp.coherence.Coherence(mdl, coherence=preset)
    coherence_score = coh.get_score()
    #print(f"COH: {preset} is : {coherence_score}.")

    #print(f"COH SCORE: {coherence_score}.")

    #coherence_per_topic = [coh.get_score(topic_id=k) for k in range(mdl.k)]
    #print('==== Coherence : {} ===='.format(preset))
    #print('Average:', average_coherence, '\nPer Topic:', coherence_per_topic)
    #print()


    return coherence_score


def get_topic_data(data_preprocessed, k):

    sentlog = globalutils.SentopLog()
     
    #print("Getting topics for size ", k)
    mdl = tp.LDAModel(seed=1, min_df=5, rm_top=0, k=k)  

    for row in data_preprocessed:
        if not row:
            print(f"GOT BLANK ROW-2!! QUIT! -- '{row}'")
            row = "NA"
        try:
            mdl.add_doc(row.strip().split())
        except Exception as e:
            print("except row: ", row)
            globalutils.show_stack_trace(str(e))

    mdl.burn_in = 100
    mdl.train(0)

    for i in range(0, 100, 10):
        mdl.train(10)
        #print('Iteration: {}\tLog-likelihood: {}'.format(i, mdl.ll_per_word))

    #print("dist: ", mdl.get_topic_word_dist)
    '''
    for i in range(mdl.k):
        #print('Top words of topic #{}'.format(k))
        print(mdl.get_topic_words(i, top_n=10))

    mdl.summary()
    '''

    i = 1
    topic_per_row = []
    for doc in mdl.docs:
        #print("DOC: ", i)
        #print("DOC TOPCS: ", doc.get_topics(5))
        highest_topic_list =  doc.get_topics(1)
        #print("HIGHEST TOPIC LIST: ", highest_topic_list)
        highest_topic_tuple = highest_topic_list[0]
        #print("HIGHEST TOPIC TUPLE: ", highest_topic_tuple)
        highest_topic_val = highest_topic_tuple[0]
        #print("HIGHEST TOPIC VAL: ", highest_topic_val)
        topic_per_row.append(highest_topic_val)
        i = i + 1

    #print("Creating topic info")
   
    topics_list = []
    for n in range (0, mdl.k):
        sentlog.append(f"Topic: {n}")
        words_list = []
        weights_list = []
        words = mdl.get_topic_words(n, top_n=config.NUM_WORDS_PER_TOPIC)
        for word in words:
            #print("word: ", word)
            words_list.append(word[0])
            weights_list.append(str(word[1]))
            sentlog.append("- " + word[0] + ", " + str(word[1]))

        topic = config.Topic(n, words_list, weights_list)
        topics_list.append(topic)

    return topic_per_row, topics_list, None


def bert_to_wordnet_pos_tag(bert_tag):
    if bert_tag.startswith('J'):
        return wordnet.ADJ
    elif bert_tag.startswith('V'):
        return wordnet.VERB
    elif bert_tag.startswith('N'):
        return wordnet.NOUN
    elif bert_tag.startswith('R'):
        return wordnet.ADV
    else:          
        return None


'''
# LDA performs additional preprocessing by removing some words and punctuation
# to surface only the most salient words:
# - Removes all punctuation from a doc.
# - Removes any word with less than 2 characters from a doc.
# - Lowercases all words in a doc.
# - Removes all words found in the stop words list.
def clean_stop(data_list, stop_words):

    cleaned = []
    for text in data_list:
        # Remove all punctuation (NOTE: this is not removing some periods for some reason)
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()   
        cleaned_sentence = ""
        for word in words:
            word = word.lower()
            if not word in stop_words and not word.isdigit() and len(word) > 2   :
                    cleaned_sentence = cleaned_sentence + " " + word

        if not cleaned_sentence:
            # We don't want empty docs at this point, so use orig text.
            cleaned_sentence = text.lower()
            print(f"WARNING! Cleaning resulted in empty text. Using orig text: {cleaned_sentence}.")
        cleaned.append(cleaned_sentence)

    return cleaned
'''

def check_duplicate_words_across_topics(topics_list):
    duplicate_words = []
    for topic in topics_list:
        #print("Checking duplicates Topic i=", i)
        words = topic.words
        for word in words:
            for topic2 in topics_list:
                if (topic != topic2):
                    #print("Checking duplicates Topic j=", j)
                    words2 = topic2.words
                    #print("Checking topic ", i, " word: ", word[0], " in topic ", j)
                    for word2 in words2:
                        #print("Checking if ", word[0], " == ", word2[0])
                        if word == word2:
                            #print("Found duplicate: ", word[0])
                            if word not in duplicate_words:
                                duplicate_words.append(word)
    #print("Found duplicate words across topics: ", duplicate_words)
    return duplicate_words


# Do not remove duplicate/overlapping terms since Venn Diagrams will be able to 
# show which terms overlap.
def get_topics(data_list, all_stop_words):
    sentlog = globalutils.SentopLog()
    #sentlog.append("----------------------------------------------------------")
    print("Assessing LDA (Tomotopy)")

    # ------------------------- PREPROCESS DOCS -------------------------

    # Get stop words
    #stop_words = globalutils.get_stopwords_list(user_stop_words)
    # Lemmatizer does not work well
    #lmtzr = WordNetLemmatizer()
    #data_preprocessed = []
    #pat = re.compile('[a-z]{2,}$')

    data_preprocessed = data_cleaner.topic_modeling_clean_stop(data_list, all_stop_words)
    #data_preprocessed = lemmatize(data_preprocessed, stop_words)


    # ------------------------- GET COHERENCE SCORES -------------------------

    # Get coherence scores for topics sizes 2-n
    sentlog.append(f"<b>&#8226; Assessments:</b>")
    sentlog.append(f"<pre>")

    highest_topic_coherence = -999999.99
    highest_coherence_topic_num = -999
    for k in range(2, 11):
        topic_coherence_score = get_coherence(data_preprocessed, k)
        #print("Coh score for %s is %s", k, topic_coherence_score)
        sentlog.append(f"- k: {k}, Coherence Score: {topic_coherence_score}")

        if topic_coherence_score > highest_topic_coherence:
            highest_topic_coherence = topic_coherence_score
            highest_coherence_topic_num = k

    sentlog.append(f"</pre>")

    # -------- GET TOPICS FOR FOR K WITH HIGHEST COHERENCE SCORE --------

    sentlog.append(f"<b>&#8226; Final Topics:</b><br>")
    sentlog.append("<pre>")

    sentlog.append(f"- Num topics: {highest_coherence_topic_num}")
    sentlog.append(f"- Coherence score: {highest_topic_coherence}")
    sentlog.append("")

    topics_per_rows, topics_list, error = get_topic_data(data_preprocessed, highest_coherence_topic_num)
    sentlog.append("</pre>")

    duplicate_words_across_topics = check_duplicate_words_across_topics(topics_list)

    sentlog.append(f"<b>&#8226; Final num topic word overlap:</b> {len(duplicate_words_across_topics)}<br>")
    sentlog.append(f"<b>&#8226; Final topic word overlap:</b>")
    sentlog.append("<pre>")
    for x in duplicate_words_across_topics:
        sentlog.append(f"- {x}")
    sentlog.append("</pre>")

    #sentlog.append(f"Common words across topics: {duplicate_words_across_topics}.\n")

    topic_model_results = config.TopicModelResults(topics_per_rows, topics_list, duplicate_words_across_topics)

    return topic_model_results, error
    
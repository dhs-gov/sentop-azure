import logging
from sklearn.feature_extraction.text import CountVectorizer
from bertopic import BERTopic
from flair.embeddings import TransformerDocumentEmbeddings
from . import config_topic_mod
from globals import globalutils
from globals import globalvars
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from database import postgres
from . import config_topic_mod as config     

class Topic:
    def __init__(self, topic_num, words, weights):
        self.topic_num = topic_num
        self.words = words
        self.weights = weights


def check_duplicate_words_across_topics(topic_model, topics_no_duplicates):
    duplicate_words = []
    for i in topics_no_duplicates:
        #print("Checking duplicates Topic i=", i)
        words = topic_model.get_topic(i)
        for word in words:
            for j in topics_no_duplicates:
                if (i != j):
                    #print("Checking duplicates Topic j=", j)
                    words2 = topic_model.get_topic(j)
                    #print("Checking topic ", i, " word: ", word[0], " in topic ", j)
                    for word2 in words2:
                        #print("Checking if ", word[0], " == ", word2[0])
                        if word[0] == word2[0]:
                            #print("Found duplicate: ", word[0])
                            if word[0] not in duplicate_words:
                                duplicate_words.append(word[0])
    #print("Found duplicate words across topics: ", duplicate_words)
    return duplicate_words


def get_topics_words_list(topic_per_row, topic_model):
    sentlog = globalutils.SentopLog()
    sentlog.append(" ")
    topics_no_duplicates = []
    for t in topic_per_row:
        if t not in topics_no_duplicates:
            topics_no_duplicates.append(t)

    #duplicate_words_across_topics = check_duplicate_words_across_topics(topic_model, topics_no_duplicates)
    #print("BERTopic duplicates: ", duplicate_words_across_topics)
   
    topics_list = []
    print(f"Num topics: {len(topics_no_duplicates)}")
    for n in topics_no_duplicates:
        sentlog.append(f"BERTopic topic: {n}")
        words_list = []
        weights_list = []

        words = topic_model.get_topic(n)
        for word in words:
            words_list.append(word[0])
            weights_list.append(str(word[1]))
            sentlog.append("- " + word[0] + ", " + str(word[1]))

        topic = Topic(n, words_list, weights_list)
        topics_list.append(topic)

    # Show most frequent topics
    #sentlog.append("Topic Distribution:")
    sentlog.append(f"\n{topic_model.get_topic_freq().head()}")

    return topics_list


def get_topic_overlap_words(topic_per_row, topic_model):
    sentlog = globalutils.SentopLog()
    sentlog.append(" ")
    topics_no_duplicates = []
    for t in topic_per_row:
        if t not in topics_no_duplicates:
            topics_no_duplicates.append(t)

    duplicate_words_across_topics = check_duplicate_words_across_topics(topic_model, topics_no_duplicates)
    sentlog.append(f"BERTopic topic overlap: {len(duplicate_words_across_topics)} words: {duplicate_words_across_topics}")
    return duplicate_words_across_topics


# Run all the models to get the best model under MAX_OUTLIERS_PERCENT
# in order of highest number of topics with lowest number of overlapping
# topic words.
# NOTE: We don't necessarily want a model with NO outliers because this 
# may mean that outliers are forced into a topic, skewing the most salient
# top words for each topic. Allowing for some outliers permits more 
# focused topics (i.e., topics comprising more salient words) 
def get_top_model(rows, all_stop_words):

    sentlog = globalutils.SentopLog()

    final_topic_model = None
    final_topic_per_row = None
    top_model = None
    top_num_topics = 0
    top_num_outliers = 999
    top_outlier_perc = 999.9
    top_num_duplicate_words = 999
    final_topics_list = []
    duplicate_words = []

    # Iterate through models until no (or low number of) outliers found
    embedding_models = ['xlm-roberta-large-finetuned-conll03-english',\
        'sentence-transformers/LaBSE',\
        'bert-base-uncased',\
        'xlm-roberta-base',\
        'distilbert-base-uncased',\
        'sentence-transformers/bert-base-nli-max-tokens',\
        'sentence-transformers/bert-base-nli-mean-tokens',\
        'roberta-large',\
        'T-Systems-onsite/cross-en-de-roberta-sentence-transformer']

    # Selects the first model that satisfies the requirements.
    for model in embedding_models:
        sentlog.append("* * * * * * * * * * * * * * * * * * * * * * * * * * *")
        sentlog.append(f"Analyzing model: {model}")

        # Prepare custom models
        #hdbscan_model = HDBSCAN(min_cluster_size=40, metric='euclidean', cluster_selection_method='eom', prediction_data=True)
        #umap_model = UMAP(n_neighbors=15, n_components=10, min_dist=0.0, metric='cosine')
        vectorizer_model = CountVectorizer(ngram_range=(1, 2), stop_words=all_stop_words)
        embedding_model = TransformerDocumentEmbeddings(model)   
        topic_model = BERTopic(
            top_n_words=config.NUM_WORDS_PER_TOPIC,\
            calculate_probabilities=True,\
            embedding_model=embedding_model,\
            vectorizer_model=vectorizer_model)

        # Set random seed OFF by setting to int
        topic_model.umap_model.random_state = 42

        topic_per_row = None
        try:
            topic_per_row, probs = topic_model.fit_transform(rows)
            #print("PROBS: %s", probs)
            if not topic_per_row:
                # Topics could not be generated
                sentlog.append(f"Could not generate topics using {model}.")
                continue
        except ValueError:  #raised if `y` is empty.
            print("Warning: topics has size 0, probably not enough data.")
            continue

        #print(f"Num topics per rows: {len(topic_per_row)}")
        unique_topics = np.unique(topic_per_row)
        num_unique_topics = len(unique_topics)
        
        outlier_topic = None
        outlier_num = 0.0
        outlier_perc = 0.0

        #print("Checking for outlier topic")
        outlier_topic = topic_model.get_topic(-1)
        if outlier_topic:
            num_unique_topics = num_unique_topics - 1  # Don't count outlier as a topic
            outlier_num = int(topic_model.get_topic_freq(-1))
            sentlog.append(f"Num outliers: {outlier_num}")
            outlier_perc = outlier_num / len(rows)
            sentlog.append(f"Max percent outliers permitted: {config.MAX_OUTLIERS_PERCENT} ({config.MAX_OUTLIERS_PERCENT * len(rows)} of {len(rows)} docs).")
            sentlog.append(f"Outlier percent: {outlier_perc}.")
        else:
            sentlog.append("No outliers found.")

        if outlier_perc <= config.MAX_OUTLIERS_PERCENT:
            if num_unique_topics > top_num_topics:
                top_model = model
                top_num_topics = num_unique_topics
                top_num_outliers = outlier_num
                top_outlier_perc = outlier_perc
                duplicate_words = get_topic_overlap_words(topic_per_row, topic_model)
                top_num_duplicate_words = len(duplicate_words)
                final_topic_model = topic_model
                final_topic_per_row = topic_per_row
                final_topics_list = get_topics_words_list(topic_per_row, topic_model)
                sentlog.append(f"\nSetting as best model: {top_model},\n - num topics: {top_num_topics},\n - num outliers: {top_num_outliers},\n - perc outliers: {top_outlier_perc},\n - num word overlap: {top_num_duplicate_words}")

            elif num_unique_topics == top_num_topics:
                duplicate_words = get_topic_overlap_words(topic_per_row, topic_model)
                if len(duplicate_words) < top_num_duplicate_words:
                    top_model = model
                    top_num_topics = num_unique_topics
                    top_num_outliers = outlier_num
                    top_outlier_perc = outlier_perc
                    top_num_duplicate_words = len(duplicate_words)
                    final_topic_model = topic_model
                    final_topic_per_row = topic_per_row
                    final_topics_list = get_topics_words_list(topic_per_row, topic_model)
                    sentlog.append(f"\nSetting as best model: {top_model},\n - num topics: {top_num_topics},\n - num outliers: {top_num_outliers},\n - perc outliers: {top_outlier_perc},\n - num word overlap: {top_num_duplicate_words}")
 
                else:
                    sentlog.append(f"Num duplicate words ({len(duplicate_words)}) > top num duplicate words ({top_num_duplicate_words}). Ignoring model.")
            else:
                sentlog.append(f"Num topics ({num_unique_topics}) < best num topics ({top_num_topics}). Ignoring model.")
        else:
            sentlog.append(f"Outlier perc ({outlier_perc}) is > than max permitted ({config.MAX_OUTLIERS_PERCENT}). Ignoring model.")

    if not top_model:
        return None, None, None, None, None, "No final topic model was determined."
    elif not final_topic_model:
        return None, None, None, None, None, "No final topic model was determined."
    elif not final_topic_per_row:
        return None, None, None, None, None, "No final topic per row was determined."
        
    sentlog.append("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    sentlog.append(f"Final model: {top_model},\n - num topics: {top_num_topics},\n - num outliers: {top_num_outliers},\n - perc outliers: {top_outlier_perc},\n - num word overlap: {top_num_duplicate_words}")

    return top_model, final_topic_model, final_topic_per_row, final_topics_list, duplicate_words, None


def get_topics(rows, all_stop_words):

    sentlog = globalutils.SentopLog()
    sentlog.append("----------------------------------------------------------")
    sentlog.append("Assessing BERTopic")
    sentlog.append("BERTopic tests several NLP sentence embedding models and selects the model that has an outlier frequency less than 20% and with the highest number of topics and lowest number of overlapping words.")

    model, topic_model, topic_per_row, topics_list, duplicate_words, error = get_top_model(rows, all_stop_words)
    if error:
        return None, None, None, error

    print(f"Using embedding model: {model}")
    final_topics_list = get_topics_words_list(topic_per_row, topic_model)

    return topic_per_row, topics_list, duplicate_words, None





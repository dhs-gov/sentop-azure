from sklearn.feature_extraction.text import CountVectorizer
from bertopic import BERTopic
from flair.embeddings import TransformerDocumentEmbeddings
from globals import globalutils
import numpy as np
from nltk.tokenize import word_tokenize
from . import config_topic_mod as config     
from globals import sentop_log

def check_best_overlapping_words_across_topics(topic_model, topics_no_duplicates):
    best_overlapping_words = []
    for i in topics_no_duplicates:
        words = topic_model.get_topic(i)
        for word in words:
            for j in topics_no_duplicates:
                if (i != j):
                    words2 = topic_model.get_topic(j)
                    for word2 in words2:
                        if word[0] == word2[0]:
                            if word[0] not in best_overlapping_words:
                                best_overlapping_words.append(word[0])
    return best_overlapping_words


def get_topics_words_list(topic_per_row, topic_model, print_topics):
    sentlog = sentop_log.SentopLog()
    topics_no_duplicates = []
    for t in topic_per_row:
        if t not in topics_no_duplicates:
            topics_no_duplicates.append(t)

    topics_list = []
    print(f"Num topics: {len(topics_no_duplicates)}")
    if print_topics:
        sentlog.info(f"<pre>", html_tag='other')
    for n in topics_no_duplicates:
        if print_topics:
            sentlog.info(f"Topic: {n}", html_tag='p')
        words_list = []
        weights_list = []

        words = topic_model.get_topic(n)
        for word in words:
            words_list.append(word[0])
            weights_list.append(str(word[1]))
            if print_topics:
                sentlog.info("- " + word[0] + ", " + str(word[1]), html_tag='p')

        topic = config.Topic(n, words_list, weights_list)
        topics_list.append(topic)

    # Show most frequent topics
    if print_topics:
        sentlog.info(f"\n{topic_model.get_topic_freq()}", html_tag='p') # .head()
        sentlog.info(f"</pre>", html_tag='other')
    return topics_list


def get_topic_overlap_words(topic_per_row, topic_model):
    sentlog = sentop_log.SentopLog()
    topics_no_duplicates = []
    for t in topic_per_row:
        if t not in topics_no_duplicates:
            topics_no_duplicates.append(t)

    best_overlapping_words_across_topics = check_best_overlapping_words_across_topics(topic_model, topics_no_duplicates)
    return best_overlapping_words_across_topics


# Run all the models to get the best model with the following criteria:
# - Lowest number of outliers (since all responses are important).
# - Lowest number of overlapping topic words (for most distinct topics).
# - Highest number of topics (since more topics means more distinct topics).

# NOTE: We don't necessarily want a model with NO outliers because this 
# may mean that outliers are forced into a topic, skewing the most salient
# top words for each topic. Allowing for some outliers permits more 
# focused topics (i.e., topics comprising more salient words).
def get_best_model_name(rows, all_stop_words):

    sentlog = sentop_log.SentopLog()

    best_topic_model = None
    best_topic_per_row = None
    best_model_name = None
    best_num_topics = 0
    best_num_outliers = 999
    best_outlier_perc = 999.9
    best_num_overlapping_words = 999
    best_topics_list = []
    best_overlapping_words = []

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

    sentlog.info(f"Assessments|", html_tag='keyval')
    sentlog.info(f"<pre>", html_tag='other')

    for model_name in embedding_models:
        # Prepare custom models
        #hdbscan_model = HDBSCAN(min_cluster_size=40, metric='euclidean', cluster_selection_method='eom', prediction_data=True)
        #umap_model = UMAP(n_neighbors=15, n_components=10, min_dist=0.0, metric='cosine')
        vectorizer_model = CountVectorizer(ngram_range=(1, 2), stop_words=all_stop_words)
        embedding_model = TransformerDocumentEmbeddings(model_name)   
        topic_model = BERTopic(
            top_n_words=config.NUM_WORDS_PER_TOPIC,\
            calculate_probabilities=True,\
            embedding_model=embedding_model,\
            vectorizer_model=vectorizer_model)

        # Set random seed OFF by setting to int
        topic_model.umap_model.random_state = 42

        topic_per_row = None
        try:
            # IMPORTANT! The following can lead to 'int too big to convert'
            # errors. To fix, set self.tokenizer.model_max_length = 512
            # in .venv/Lib/site-packages/flair/embeddings/document.py: line 59.
            topic_per_row, probs = topic_model.fit_transform(rows)
            #print("BERTopic topics: %s", topic_per_row)
            #print("BERTopic PROBS: %s", probs)
            if not topic_per_row:
                # Topics could not be generated
                sentlog.warn(f"Could not generate topics using model {model_name}.")
                continue
        except Exception as e:  #raised if `y` is empty.
            globalutils.show_stack_trace(f"BERTopic could not generate topics or probabilities with model {model_name}: {str(e)}.")
            continue

        unique_topics = np.unique(topic_per_row)
        num_unique_topics = len(unique_topics)
        
        outlier_num = 0
        outlier_perc = 0.00000
        num_overlapping_words = 0

        outlier_topic = topic_model.get_topic(-1)
        if outlier_topic:
            num_unique_topics = num_unique_topics - 1  # Don't count outlier as a topic
            outlier_num = int(topic_model.get_topic_freq(-1))
            outlier_perc = outlier_num / len(rows)

        # Compare against best model and replace if better.
        if outlier_perc < best_outlier_perc:
            #sentlog.append("Trace outlier_perc <= best_outlier_perc")
            best_model_name = model_name
            best_num_topics = num_unique_topics
            best_num_outliers = outlier_num
            best_outlier_perc = outlier_perc
            best_overlapping_words = get_topic_overlap_words(topic_per_row, topic_model)
            num_overlapping_words = len(best_overlapping_words)
            best_num_overlapping_words = len(best_overlapping_words)
            best_topic_model = topic_model
            best_topic_per_row = topic_per_row
            best_topics_list = get_topics_words_list(topic_per_row, topic_model, False)

        elif outlier_perc == best_outlier_perc:

            overlapping_words = get_topic_overlap_words(topic_per_row, topic_model)
            num_overlapping_words = len(overlapping_words)

            if len(overlapping_words) < best_num_overlapping_words:
                best_model_name = model_name
                best_num_topics = num_unique_topics
                best_num_outliers = outlier_num
                best_outlier_perc = outlier_perc
                best_overlapping_words = overlapping_words
                best_num_overlapping_words = len(best_overlapping_words)
                best_topic_model = topic_model
                best_topic_per_row = topic_per_row
                best_topics_list = get_topics_words_list(topic_per_row, topic_model, False)
            
            elif len(overlapping_words) == best_num_overlapping_words:
                if num_unique_topics > best_num_topics:
                    best_model_name = model_name
                    best_num_topics = num_unique_topics
                    best_num_outliers = outlier_num
                    best_outlier_perc = outlier_perc
                    best_overlapping_words = overlapping_words
                    best_num_overlapping_words = len(best_overlapping_words)
                    best_topic_model = topic_model
                    best_topic_per_row = topic_per_row
                    best_topics_list = get_topics_words_list(topic_per_row, topic_model, False)
      
        sentlog.info(f"- Model: {model_name}, Outliers: {outlier_num}, Topics: {num_unique_topics}, Overlap: {num_overlapping_words}", html_tag='p')

    sentlog.info("</pre>", html_tag='other')

    if not best_model_name:
        return None, None, None, None, None, "No final topic model was determined."
    elif not best_topic_model:
        return None, None, None, None, None, "No final topic model was determined."
    elif not best_topic_per_row:
        return None, None, None, None, None, "No final topic per row was determined."
        
    sentlog.info(f"Final Topics|{best_model_name}", html_tag='keyval')
    sentlog.info("<pre>", html_tag='other')
    sentlog.info(f"- num topics: {best_num_topics}", html_tag='p')
    sentlog.info(f"- num outliers: {best_num_outliers}", html_tag='p')
    sentlog.info(f"- perc outliers: {best_outlier_perc}", html_tag='p')
    sentlog.info(f"- num word overlap: {best_num_overlapping_words}", html_tag='p')
    sentlog.info("</pre>", html_tag='other')

    return best_model_name, best_topic_model, best_topic_per_row, best_topics_list, best_overlapping_words, None


def get_topics(rows, all_stop_words):

    sentlog = sentop_log.SentopLog()
    sentlog.info("BERTopic", html_tag='h2')
    sentlog.info("SENTOP assesses BERTopic topics using multiple NLP sentence embedding models. The final topics are selected based on the model that has (1) the lowest number of outliers, (2) the lowest topic word overlap, and (3) the highest number of topics.<br><br>", html_tag='p')
    sentlog.info("URL|<a href=\"https://github.com/MaartenGr/BERTopic\">https://github.com/MaartenGr/BERTopic</a><br>", html_tag='keyval')

    model, topic_model, topic_per_row, topics_list, best_overlapping_words, error = get_best_model_name(rows, all_stop_words)
    if error:
        return None, None, None, error

    best_topics_list = get_topics_words_list(topic_per_row, topic_model, True)

    sentlog.info(f"Final num topic word overlap|{len(best_overlapping_words)}", html_tag='keyval')
    sentlog.info(f"Final topic word overlap|", html_tag='keyval')
    sentlog.info("<pre>", html_tag='other')
    for x in best_overlapping_words:
        sentlog.info(f"- {x}", html_tag='p')
    sentlog.info("</pre>", html_tag='other')
    
    topic_model_results = config.TopicModelResults(topic_per_row, topics_list, best_overlapping_words)

    return topic_model_results, None





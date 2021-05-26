import logging
from collections import Counter
from adaptnlp import EasySequenceClassifier
from topic_modeling import topmod_bertopic
from topic_modeling import lda_tomotopy
from sentiment_analysis import class3 
from sentiment_analysis import class5 

from globals import globalutils
import json
import jsonpickle
from database import postgres
import sentop_config as config
import time

class Result:
    def __init__(self, result, bert_topics, lda_topics):
        self.result = result
        self.bert_topics = bert_topics
        self.lda_topics = lda_topics


class Paragraph:
    def __init__(self, text, bertopic, lda, class3, star5):
        self.text = text
        self.bertopic = bertopic
        self.lda = lda
        self.class3 = class3
        self.star5 = star5


class Topic:
    def __init__(self, topic_num, word_weight):
        self.topic_num = topic_num
        self.word_weight = word_weight


class Word:
    def __init__(self, word, weight):
        self.word = word
        self.weight = weight


def get_sentiments(data_list, sentlog):
    sentlog = globalutils.SentopLog()
    classifier = EasySequenceClassifier()
    class3_sentiment_rows = class3.assess(classifier, data_list)
    sentlog.append("Done")
    star5_sentiment_rows = class5.assess(classifier, data_list)
    sentlog.append("Done")
    #emotion.assess(data_list)
    #sentlog.append("Done")

    return class3_sentiment_rows, star5_sentiment_rows


class Response:
    def __init__(self, sentop_id):
        self.sentop_id = sentop_id

        self.results_tablename = sentop_id + "_results"
        self.bertopic_tablename = sentop_id + "_bertopic_words"
        self.lda_tablename = sentop_id + "_lda_words"

        self.results_filename = sentop_id + "_results.xlsx"
        self.log_filename = sentop_id + "_log.txt"

# ================================== M A I N ===================================

# Here, 'name' is the incoming data_in payload.
def main(name: object) -> json:

    start = time.time()
    sentlog = globalutils.SentopLog()
    sentlog.append("*** If this line appears more than once, then Azure Function replay has occurred! ***\n")
    sentlog.append("----------------------------------------------------------")

    json_obj = name
    data_in_obj = jsonpickle.decode(json_obj)
    kms_id = data_in_obj.kms_id
    sentop_id = data_in_obj.sentop_id
    sentlog.append(f"Starting analysis for SENTOP ID: {sentop_id}")
    data_list = data_in_obj.data_list
    #sentlog.append("data_list in activity: ", data_list)
    all_stop_words = data_in_obj.all_stop_words
    #sentlog.append("User stop words in activity: ", all_stop_words)
    row_id_list = data_in_obj.row_id_list
    #sentlog.append("row_id_list words in activity: ", row_id_list)
    annotation = data_in_obj.annotation
    sentlog.append(f"Annotation found : {annotation}")

    # ---------------------------- GET SENTIMENTS ------------------------------

    # Perform sentiment analyses
    class3_sentiment_rows, star5_sentiment_rows = get_sentiments(data_list, sentlog)
    
    # ----------------------------- GET BERTopic -------------------------------

    # Perform BERTopic
    bert_sentence_topics, bert_topics, bert_duplicate_words, bert_error = topmod_bertopic.get_topics(
        data_list, all_stop_words)

    if bert_error:
        sentlog.append(f"ERROR! {bert_error}.\n")
    elif bert_topics:
        #sentlog.append("Num bert topics: ", len(bert_topics))
        #sentlog.append(f"BERTopic topics {bert_topics}.\n")
        db = postgres.Database()
        db.create_bertopic_table(sentop_id, bert_topics)
        db.create_bertopic_nooverlap_table(sentop_id, bert_topics, bert_duplicate_words)
    else:
        sentlog.append(f"ERROR! No BERTopic topics could be generated.\n")

    # -------------------------------- GET LDA ---------------------------------

    # Perform LDA
    lda_sentence_topics, lda_topics, lda_duplicate_words, lda_error = lda_tomotopy.get_topics(
        data_list, all_stop_words)

    if lda_error:
        sentlog.append(f"ERROR! {lda_error}.\n")
    elif lda_topics:
        #sentlog.append(f"LDA topics {lda_topics}.\n")
        db = postgres.Database()
        db.create_lda_table(sentop_id, lda_topics)
        db.create_lda_nooverlap_table(sentop_id, lda_topics, lda_duplicate_words)

        if not lda_error:
            sentlog.append(f"LDA Topic Distribution: {Counter(lda_sentence_topics)}.\n")
    else:
        sentlog.append("WARNING: No LDA topics could be generated.")

    #sentlog.append("class3-rows: ", len(class3_sentiment_rows))
    #sentlog.append("class5-rows: ", len(star5_sentiment_rows))

    # ----------------------------- RESULTS TO DB ------------------------------

    # Write to database
    db = postgres.Database()
    db.create_result_table(sentop_id, row_id_list, data_list, class3_sentiment_rows, star5_sentiment_rows, bert_sentence_topics, bert_topics, lda_sentence_topics, lda_topics)
    
    sentlog.append("----------------------------------------------------------")
    sentlog.append(f"Created PostgreSQL tables for SENTOP ID: {sentop_id}")

    # ---------------------------- RESULTS TO XLSX -----------------------------

    globalutils.generate_excel(sentop_id, annotation, row_id_list, data_list, bert_sentence_topics, lda_sentence_topics, class3_sentiment_rows, star5_sentiment_rows, bert_topics, lda_topics, bert_duplicate_words, lda_duplicate_words)

    sentlog.append(f"Generated Excel files for SENTOP ID: {sentop_id}")

    # -------------------------------- FINISH ----------------------------------

    result = Response(sentop_id)

    json_out = jsonpickle.encode(result, unpicklable=False)
    #sentlog.append("JSON STR OUT: ", json_out)
    sentlog.append(f"Completed processing: {kms_id} (SENTOP ID: {sentop_id}).")
    end = time.time() 

    hours, rem = divmod(end-start, 3600)
    minutes, seconds = divmod(rem, 60)
    sentlog.append("Elapsed {:0>2}h {:0>2}m {:05.1f}s".format(int(hours),int(minutes),seconds))
    sentlog.append(f"DONE")

    if json_out:
        print("<<<<<<<<<<<<<<<<<<< E N D <<<<<<<<<<<<<<<<<<<")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return json_out
    else:
        sentlog.append("ERROR! Unknown error performing sentiment analysis and topic modeling.")
        print("<<<<<<<<<<<<<<<<<<< E N D <<<<<<<<<<<<<<<<<<<")
        return "Unknown error performing sentiment analysis and topic modeling."



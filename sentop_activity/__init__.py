from base64 import standard_b64decode
from collections import Counter
from adaptnlp import EasySequenceClassifier
from topic_modeling import topmod_bertopic
from topic_modeling import lda_tomotopy
from sentiment_analysis import class3 
from sentiment_analysis import class5 
from sentiment_analysis import emotion1 
from sentiment_analysis import emotion2
from question_answer import qa_adaptnlp
#from sentiment_analysis import hate -- couldn't detect hate
#from sentiment_analysis import irony -- lots of false positives/negatives
from sentiment_analysis import offensive1 

from globals import globalutils
import json
import jsonpickle
from database import postgres
import sentop_config as config
import time
from globals import sentop_log


class Sentiments:
    def __init__(self, id, name, nlp_model_name, type_name, data_list):
        self.id = id
        self.name = name
        self.nlp_model_name = nlp_model_name
        self.type_name = type_name
        self.data_list = data_list


def get_sentiments(data_list, sentlog): 
    sentlog = sentop_log.SentopLog()
    classifier = EasySequenceClassifier()
    sentiment_results = []

    class3_results = class3.assess(classifier, data_list)
    sentiment_results.append(class3_results)

    class5_results = class5.assess(classifier, data_list)
    sentiment_results.append(class5_results)

    emotion_results = emotion1.assess(classifier, data_list)
    sentiment_results.append(emotion_results)

    offensive_results = offensive1.assess(classifier, data_list)
    sentiment_results.append(offensive_results)

    emotion2_results = emotion2.assess(classifier, data_list)
    sentiment_results.append(emotion2_results)

    return sentiment_results


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
    sentlog = sentop_log.SentopLog()
    sentlog.info("<br><hr>", html_tag='other')
    sentlog.info("<div style=\"text-align: center; color: #e97e16; \">*** If this line appears more than once, then Azure Function replay has occurred! ***</div>\n", html_tag='p')
    sentlog.info("<hr>", html_tag='other')

    json_obj = name
    data_in_obj = jsonpickle.decode(json_obj)
    kms_id = data_in_obj.kms_id
    sentop_id = data_in_obj.sentop_id
    #sentlog.append(f"Starting analysis for SENTOP ID: {sentop_id}")
    data_list = data_in_obj.data_list
    #sentlog.append("data_list in activity: ", data_list)
    all_stop_words = data_in_obj.all_stop_words
    #sentlog.append("User stop words in activity: ", all_stop_words)
    row_id_list = data_in_obj.row_id_list
    #sentlog.append("row_id_list words in activity: ", row_id_list)
    annotation = data_in_obj.annotation
    #sentlog.append(f"Annotation found : {annotation}")

    # --------------------------- SENTIMENT ANALYSIS ---------------------------
    sentlog.info("Sentiment Analyses", html_tag='h1')

    # Perform sentiment analyses
    sentiment_results = get_sentiments(data_list, sentlog)

    #for r in sentiment_results:
    #    print(f"Got id: {r.id}")
    #    print(f"GOt list: {r.data_list}")

    # ------------------------- GET Question Answer ----------------------------

    #qa.assess(data_list)
    question = "What is the problem?"
    print("Question: ", question)
 
    # The QA models results in VS Code 'func host start' termination.
    #qa_adaptnlp.assess(data_list)
    #for result in results:
    #    print(f"QA result: {result.answer},  confidence: {result.score} ")

    # ---------------------------- TOPIC MODELING ------------------------------
   
    sentlog.info("<hr>", html_tag='other')
    sentlog.info("Topic Modeling", html_tag='h1')

    # ---------------------------------- LDA -----------------------------------
 
    sentlog.info("Tomotopy (LDA)", html_tag='h2')
    sentlog.info("SENTOP assesses Tomotopy coherence scores for topic sizes <i>k</i>=2..10. The topic size <k> with the highest coherence score is selected as the final LDA topic size.<br><br>", html_tag='p')
    sentlog.info("URL|<a href=\"https:/https://github.com/bab2min/tomotopy\">https://github.com/bab2min/tomotopy</a>", html_tag='keyval')

    # Perform LDA
    lda_results, lda_error = lda_tomotopy.get_topics(
        data_list, all_stop_words)

    if lda_error:
        sentlog.error(f"{lda_error}")
    elif lda_results.topics_list:
        #sentlog.append(f"LDA topics {lda_topics}.\n")
        db = postgres.Database()
        db.create_lda_table(sentop_id, lda_results.topics_list)
        db.create_lda_nooverlap_table(sentop_id, lda_results.topics_list, lda_results.duplicate_words_across_topics)

        #if not lda_error:
        #    sentlog.append(f"LDA Topic Distribution: {Counter(lda_sentence_topics)}.\n")
    else:
        sentlog.warn("LDA topics could not be generated.")


    # ------------------------------- BERTopic ---------------------------------

    sentlog.info("BERTopic", html_tag='h2')
    sentlog.info("SENTOP assesses BERTopic topics using multiple NLP sentence embedding models. The final topics are selected based on the model that has (1) the lowest number of outliers, (2) the lowest topic word overlap, and (3) the highest number of topics.<br><br>", html_tag='p')
    sentlog.info("URL|<a href=\"https://github.com/MaartenGr/BERTopic\">https://github.com/MaartenGr/BERTopic</a><br>", html_tag='keyval')

    # Perform BERTopic
    bertopic_results, bert_error = topmod_bertopic.get_topics(data_list, all_stop_words)

    if bert_error:
        sentlog.error(f"{bert_error}.")
    elif bertopic_results.topics_list:
        #sentlog.append("Num bert topics: ", len(bert_topics))
        #sentlog.append(f"BERTopic topics {bert_topics}.\n")
        db = postgres.Database()
        db.create_bertopic_table(sentop_id, bertopic_results.topics_list)
        db.create_bertopic_nooverlap_table(sentop_id, bertopic_results.topics_list, bertopic_results.duplicate_words_across_topics)
    else:
        sentlog.error(f"ERROR! No BERTopic topics could be generated.")


    # ----------------------------- RESULTS TO DB ------------------------------
    sentlog.info("Status", html_tag='h2')
    # Write to database
    db = postgres.Database()
    db.create_result_table(sentop_id, row_id_list, data_list, sentiment_results, bertopic_results, lda_results)
    
    sentlog.info(f"PostgreSQL tables|Completed", html_tag='keyval')

    # ---------------------------- RESULTS TO XLSX -----------------------------

    globalutils.generate_excel(sentop_id, annotation, row_id_list, data_list, sentiment_results, bertopic_results, lda_results)

    sentlog.info(f"Excel XLSX files|Completed", html_tag='keyval')

    # -------------------------------- FINISH ----------------------------------

    result = Response(sentop_id)

    json_out = jsonpickle.encode(result, unpicklable=False)
    #sentlog.append("JSON STR OUT: ", json_out)
    sentlog.info(f"Completed processing|{kms_id}", html_tag='keyval')
    end = time.time() 

    hours, rem = divmod(end-start, 3600)
    minutes, seconds = divmod(rem, 60)
    sentlog.info("Elapsed|{:0>2}h {:0>2}m {:0>2}s".format(int(hours),int(minutes),seconds), html_tag='keyval')

    if json_out:
        print("<<<<<<<<<<<<<<<<<<< E N D <<<<<<<<<<<<<<<<<<<")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return json_out
    else:
        sentlog.error("ERROR! Unknown error performing sentiment analysis and topic modeling.")
        print("<<<<<<<<<<<<<<<<<<< E N D <<<<<<<<<<<<<<<<<<<")
        return "Unknown error performing sentiment analysis and topic modeling."



from globals import globalutils
from top2vec import Top2Vec
from data_util import data_cleaner
from . import config_topic_mod as config     

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

    MAX_TOPICS = 10

    sentlog = globalutils.SentopLog()
    print("Assessing Top2Vec")
    data_preprocessed = data_cleaner.topic_modeling_clean_stop(data_list, all_stop_words)

    if len(data_preprocessed) < 500:
        multiplier = int(500 / len(data_preprocessed))
        for i in range(multiplier):
            data_preprocessed = data_preprocessed + data_preprocessed

    #print(f"size of data for top2vec: {len(data_preprocessed)}")

    topic_per_row = []
    topics_list = []

    try:
        num_docs = len(data_preprocessed)
        model = Top2Vec(data_preprocessed)

        for i in range(num_docs):
            list = []
            list.append(i)
            x = model.get_documents_topics(doc_ids=list)
            topic_list = x[0]
            topic_num = topic_list[0]
            #print(f"Doc: {i}: topic = {topic_num}")
            topic_per_row.append(topic_num)

        #print(f"Topic per row num: {len(topic_per_row)}")
        num_topics = model.get_num_topics()

        #print(f"Top2Vec num topics: {num_topics}")
        topic_sizes, topic_nums = model.get_topic_sizes()
        #print(f"toipc sizes: {topic_sizes}, topic nums: {topic_nums}")

        topic_words, word_scores, topic_nums = model.get_topics()
        #print(f"Topic words: {topic_words}")
        num_topics = len(topic_nums)

        sentlog.append(f"<b>&#8226; Num topics:</b> {num_topics}<br>")
        if num_topics > MAX_TOPICS:
            sentlog.append(f"<div style=\"font-weight: bold; color: #e97e16; \">&#8226; WARNING! Invalid number of topics. This may happen if there is not enough valid documents for Top2Vec.</div>")
            sentlog.append(f"<div style=\"font-weight: bold; color: #e97e16; \">&#8226; WARNING! Topics not shown due to invalid number of topics. See results spreadsheet for topics.</div>")

        if num_topics <= MAX_TOPICS:
            sentlog.append("<pre>")

        for i in range (num_topics):
            if num_topics <= MAX_TOPICS:
                sentlog.append(f"Topic: {i}")
            words_list = []
            weights_list = []
            words = topic_words[i].tolist()
            #print(f"words type: {type(words)}")
            #print(f"{words}")
            scores = word_scores[i].tolist()
            #print(f"scores type: {type(scores)}")
            #print(f"{scores}")
            num_words = len(words)
            for j in range (num_words):
                words_list.append(words[j])
                weights_list.append(str(scores[j]))
                if num_topics <= MAX_TOPICS:
                    sentlog.append("- " + words[j] + ", " + str(scores[j]))

            topic = config.Topic(i, words_list, weights_list)
            topics_list.append(topic)

        if num_topics <= MAX_TOPICS:
            sentlog.append("</pre>")

        # = len(topic_per_row)
        #sentlog.append(f"TOPIC ROW LEN: {num_rows}")

        duplicate_words_across_topics = check_duplicate_words_across_topics(topics_list)
        if num_topics <= MAX_TOPICS:
            sentlog.append(f"<b>Num topic word overlap:</b> {len(duplicate_words_across_topics)}<br>")
            sentlog.append(f"<b>Topic overlap:</b><br>")
            sentlog.append("<pre>")
            for x in duplicate_words_across_topics:
                sentlog.append(f"- {x}")
            sentlog.append("</pre>")
        else:
            sentlog.append(f"<div style=\"font-weight: bold; color: #e97e16; \">&#8226; WARNING! Num topic word overlap not shown due to invalid number of topics.</div>")

        topic_model_results = config.TopicModelResults(topic_per_row, topics_list, duplicate_words_across_topics)
        return topic_model_results, None

    except Exception as e:
        sentlog.append(f"Exception with top2vec possibly due to inadequate number of documents: {e}")
        return None, None, str(e)



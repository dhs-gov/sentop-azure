import psycopg2
import sentop_config as config
from datetime import datetime
from globals import globalutils
from datetime import datetime

class Database:
    def __init__(self):
        self.url = config.database["url"]
        # print("url: ", self.url)
        self.db = config.database["database"]
        # print("db: ", self.db)
        self.username = config.database["username"]
        # print("username: ", self.username)
        self.pwd = config.database["password"]
        # print("pwd: ", self.pwd)
        self.conn = None
        self.results_table_suffix = "_results"
        self.lda_words_table_suffix = "_lda_words"
        self.bertopic_words_table_suffix = "_bertopic_words"
        self.top2vec_words_table_suffix = "_top2vec_words"

    # -------------------------------- GENERAL ----------------------------------

    def open_connection(self):
        try:
            self.conn = psycopg2.connect(host=self.url, database=self.db, user=self.username, password=self.pwd)
            self.conn.autocommit = True
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))


    def close_connection(self):
        try:
            self.conn.close()
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))


    def execute_stmt(self, sql):
        try:
            # print("Executing: ", sql)
            cur = self.conn.cursor()
            cur.execute(sql)
            self.conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(f"Error executing SQL: {sql}, {str(e)}")


    def execute_stmt_data(self, sql, data):
        try:
            # print("Executing: ", sql)
            cur = self.conn.cursor()
            cur.execute(sql, data)
            self.conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))


    def table_exists(self, tablename):
        try:
            cur = self.conn.cursor()
            stmt = "SELECT * FROM information_schema.tables WHERE table_name = '" + tablename + "'"
            cur.execute(stmt)
            self.conn.commit()
            cur.close()
            return bool(cur.rowcount)

        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))


    # Remove table
    def remove_table(self, tablename):
        #print("Removing table")
        try:
            stmt = "DROP TABLE " + tablename
            self.execute_stmt(stmt)

        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))


    # Remove all tables associated with ID
    def remove_all_tables(self, id):
        try:
            self.remove_table(id + self.results_table_suffix)
            self.remove_table(id + self.lda_words_table_suffix)
            self.remove_table(id + self.bertopic_words_table_suffix)
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))


    def add_result(self, tablename):
        try:
            print("Test")
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))


    def clear_table(self, tablename):
        print("Clearing table")
        try:
            stmt = "DELETE FROM " + tablename
            self.execute_stmt(stmt)
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))


   # ------------------------------ SUBMISSIONS -------------------------------

    def create_submissions_table(self):
        try:
            print("Creating submissions table.")
            stmt = "CREATE TABLE submissions (id text, annotation text, json_data text, file_url text, received_date timestamp, completed_date timestamp, status text, message text, PRIMARY KEY(id))"
            self.execute_stmt(stmt)
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))


    def add_submission(self, id, file_url):
        self.open_connection()
        if not self.table_exists("submissions"):
            print("Table submissions does not exist")
            self.create_submissions_table()

        # print("Adding submission")
        try:
            # Delete existing submission by both ID and file_url
            if id:
                stmt = ("DELETE FROM submissions WHERE id = '" +
                    id + "'")
                self.execute_stmt(stmt)
            elif file_url:
                stmt = ("DELETE FROM submissions WHERE file_url = '" +
                    file_url + "'")
                self.execute_stmt(stmt)
            # Add submission to submissions table
            stmt = """INSERT INTO submissions 
                (id, file_url, received_date, status) VALUES (%s,%s,%s,%s)"""
            data = (id, file_url, datetime.utcnow(), 'received')
            self.execute_stmt_data(stmt, data)
            return None
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))

        finally:
            self.close_connection()


    # Save JSON data to submissions table.
    def add_json_data(self, id, json_str):
        self.open_connection()
        # print("Adding JSON data...")
        try:
            # print("JSON STR: ", json_str)
            stmt = ("UPDATE submissions SET json_data = '" +
                json_str + "' WHERE id = '" + id + "'")
            self.execute_stmt(stmt)
            return None
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))
            return str(e)
        finally:
            self.close_connection()


    # Save Annotation data to submissions table.
    def add_annotation(self, id, annotation):
        self.open_connection()
        # print("Adding Annotation data...")
        try:
            # print("JSON STR: ", json_str)
            stmt = ("UPDATE submissions SET annotation = '" +
                annotation + "' WHERE id = '" + id + "'")
            self.execute_stmt(stmt)
            return None
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))
            return str(e)
        finally:
            self.close_connection()

   # -------------------------------- TOP2VEC WORDS ----------------------------------

    def create_top2vec_table(self, id, topics):
        tablename = str(id) + self.top2vec_words_table_suffix + "_nooverlap"
        #print("In create top2vec_table: ", tablename)

        self.open_connection()
        if self.table_exists(tablename):
            # Remove existing Top2Vec words table.
            #print("Removing top2vec table...")
            self.remove_table(tablename)
            #print("Removed existing Top2Vec words table: ", tablename)

        try:
            stmt = ("CREATE TABLE " + tablename +
                " (num int NOT NULL, topic int, word text, weight float, PRIMARY KEY (num))")
            self.execute_stmt(stmt)
            num = 0
            for topic in topics:
                #print("topic numb: ", topic.topic_num)
                for i in range(len(topic.words)):
                    # Update submissions table
                    stmt = ("INSERT INTO " + tablename +
                        "(num, topic, word, weight) VALUES (%s,%s,%s,%s)")
                    data = (num, topic.topic_num, topic.words[i], topic.weights[i])
                    self.execute_stmt_data(stmt, data)
                    num = num + 1
            #print("Created Top2Vec words table.")

        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))
        finally:
            self.close_connection()

    def create_top2vec_nooverlap_table(self, id, topics, duplicate_words):
        tablename = str(id) + self.top2vec_words_table_suffix
        #print("In create bertopics_table: ", tablename)

        self.open_connection()
        if self.table_exists(tablename):
            # Remove existing Top2Vec words table.
            #print("Removing top2vec table...")
            self.remove_table(tablename)
            #print("Removed existing Top2Vec words table: ", tablename)

        try:
            stmt = ("CREATE TABLE " + tablename +
                " (num int NOT NULL, topic int, word text, weight float, PRIMARY KEY (num))")
            self.execute_stmt(stmt)
            num = 0
            for topic in topics:
                #print("topic numb: ", topic.topic_num)
                for i in range(len(topic.words)):
                    # Update submissions table
                    if not topic.words[i] in duplicate_words:
                        stmt = ("INSERT INTO " + tablename +
                            "(num, topic, word, weight) VALUES (%s,%s,%s,%s)")
                        data = (num, topic.topic_num, topic.words[i], topic.weights[i])
                        self.execute_stmt_data(stmt, data)
                        num = num + 1
            #print("Created Top2Vec non-overlapping words table.")

        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))
        finally:
            self.close_connection()


    def get_sentiment(self, id, sentiments):
        for sentiment in sentiments:
            if sentiment.id == id:
                return sentiment

   # -------------------------------- LDA WORDS ----------------------------------

    def create_lda_table(self, id, topics):
        tablename = str(id) + self.lda_words_table_suffix
        #print("In create lda table: ", tablename)
        self.open_connection()
        if self.table_exists(tablename):
            # Remove existing BERTopic words table.
            #print("Removing lda table...")
            self.remove_table(tablename)
            #print("Removed existing LDA words table: ", tablename)

        try:
            stmt = ("CREATE TABLE " + tablename +
                "(num int NOT NULL, topic int, word text, weight float, PRIMARY KEY (num))")
            self.execute_stmt(stmt)
            num = 0
            for topic in topics:
                #print("topic numb: ", topic.topic_num)
                for i in range(len(topic.words)):
                    # Update submissions table
                    stmt = ("INSERT INTO " + tablename +
                        "(num, topic, word, weight) VALUES (%s,%s,%s,%s)")
                    data = (num, topic.topic_num, topic.words[i], topic.weights[i])
                    self.execute_stmt_data(stmt, data)
                    num = num + 1
            #print("Created LDA words table.")
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))
        finally:
            self.close_connection()

    def create_lda_nooverlap_table(self, id, topics, lda_duplicate_words):
        tablename = str(id) + self.lda_words_table_suffix + "_nooverlap"
        #print("In create lda table: ", tablename)
        self.open_connection()
        if self.table_exists(tablename):
            # Remove existing BERTopic words table.
            #print("Removing lda table...")
            self.remove_table(tablename)
            #print("Removed existing LDA words table: ", tablename)

        try:
            stmt = ("CREATE TABLE " + tablename +
                "(num int NOT NULL, topic int, word text, weight float, PRIMARY KEY (num))")
            self.execute_stmt(stmt)
            num = 0
            for topic in topics:
                #print("topic numb: ", topic.topic_num)
                for i in range(len(topic.words)):
                    if not topic.words[i] in lda_duplicate_words:
                        # Update submissions table
                        stmt = ("INSERT INTO " + tablename +
                            "(num, topic, word, weight) VALUES (%s,%s,%s,%s)")
                        data = (num, topic.topic_num, topic.words[i], topic.weights[i])
                        self.execute_stmt_data(stmt, data)
                        num = num + 1
            #print("Created LDA non-overlapping words table.")
        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))
        finally:
            self.close_connection()

    # -------------------------------- BERTOPIC WORDS ----------------------------------

    def create_bertopic_table(self, id, topics):
        tablename = str(id) + self.bertopic_words_table_suffix + "_nooverlap"
        #print("In create bertopics_table: ", tablename)

        self.open_connection()
        if self.table_exists(tablename):
            # Remove existing BERTopic words table.
            #print("Removing bertopics table...")
            self.remove_table(tablename)
            #print("Removed existing BERTopic words table: ", tablename)

        try:
            stmt = ("CREATE TABLE " + tablename +
                " (num int NOT NULL, topic int, word text, weight float, PRIMARY KEY (num))")
            self.execute_stmt(stmt)
            num = 0
            for topic in topics:
                #print("topic numb: ", topic.topic_num)
                for i in range(len(topic.words)):
                    # Update submissions table
                    stmt = ("INSERT INTO " + tablename +
                        "(num, topic, word, weight) VALUES (%s,%s,%s,%s)")
                    data = (num, topic.topic_num, topic.words[i], topic.weights[i])
                    self.execute_stmt_data(stmt, data)
                    num = num + 1
            #print("Created BERTopics words table.")

        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))
        finally:
            self.close_connection()

    def create_bertopic_nooverlap_table(self, id, topics, bert_duplicate_words):

        tablename = str(id) + self.bertopic_words_table_suffix
        #print("In create bertopics_table: ", tablename)

        self.open_connection()
        if self.table_exists(tablename):
            # Remove existing BERTopic words table.
            #print("Removing bertopics table...")
            self.remove_table(tablename)
            #print("Removed existing BERTopic words table: ", tablename)

        try:
            stmt = ("CREATE TABLE " + tablename +
                " (num int NOT NULL, topic int, word text, weight float, PRIMARY KEY (num))")
            self.execute_stmt(stmt)
            num = 0
            for topic in topics:
                #print("topic numb: ", topic.topic_num)
                for i in range(len(topic.words)):
                    # Update submissions table
                    if not topic.words[i] in bert_duplicate_words:
                        stmt = ("INSERT INTO " + tablename +
                            "(num, topic, word, weight) VALUES (%s,%s,%s,%s)")
                        data = (num, topic.topic_num, topic.words[i], topic.weights[i])
                        self.execute_stmt_data(stmt, data)
                        num = num + 1
            #print("Created BERTopics non-overlapping words table.")

        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))
        finally:
            self.close_connection()


    def get_sentiment(self, id, sentiments):
        for sentiment in sentiments:
            if sentiment.id == id:
                return sentiment

    # -------------------------------- RESULTS ----------------------------------

    def create_result_table(self, id, id_list, data_list, sentiment_results, bertopic_results, lda_results):
        sentlog = globalutils.SentopLog()

        #top2vec_sentence_topics = top2vec_results.topic_per_row
        #top2vec_topics = top2vec_results.topics_list    

        bert_sentence_topics = bertopic_results.topic_per_row
        #bertopic_topics = bertopic_results.topics_list
        lda_sentence_topics = lda_results.topic_per_row
        #lda_topics = lda_results.topics_list

        # NOTE: data is a list of [id, text]
        #num_list = globalutils.column(data, 0)
        #data_list = globalutils.column(data, 1)
        
        #print("In create bertopics_table")
        tablename = str(id) + self.results_table_suffix
        self.open_connection()
        if self.table_exists(tablename):
            # Remove existing results table.
            #print("Removing results table...")
            self.remove_table(tablename)
            #print("Removed existing results table: ", tablename)

        class3 = self.get_sentiment('class3', sentiment_results)
        class5 = self.get_sentiment('class5', sentiment_results)
        emotion1 = self.get_sentiment('emotion1', sentiment_results)
        offensive1 = self.get_sentiment('offensive1', sentiment_results)
        emotion2 = self.get_sentiment('emotion2', sentiment_results)

        try:
            sentlog.append(f"Creating table: {tablename}")
            stmt = ("CREATE TABLE " + tablename + 
                " (num text NOT NULL, document text, class3 text, class5 text, emotion1 text, emotion2 text, offensive1 text, lda text, bertopic text, PRIMARY KEY (num))")
            self.execute_stmt(stmt)
            #num = 0
            sentlog.append(f"Executed creating: {tablename}")

            for i in range(len(data_list)):
                bert_topic = None
                if bert_sentence_topics:
                    bert_topic = bert_sentence_topics[i]
                lda_topic = None
                if lda_sentence_topics:
                    lda_topic = lda_sentence_topics[i]
                #top2vec_topic = None
                #if top2vec_sentence_topics:
                #    top2vec_topic = top2vec_sentence_topics[i]

                if (data_list[i]):
                    #print("3Class: ", class3_sentiment_rows[i].sentiment)
                    #print("5Class: ", star5_sentiment_rows[i].sentiment)

                    stmt = ("INSERT INTO " + tablename + "(num, document, class3, class5, emotion1, emotion2, offensive1, lda, bertopic) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                    data = (id_list[i], data_list[i], class3.data_list[i], class5.data_list[i], emotion1.data_list[i], emotion2.data_list[i], offensive1.data_list[i], lda_topic, bert_topic)
                    self.execute_stmt_data(stmt, data)

                #num = num + 1
            print("Combined sentiment and topics.")

        except (Exception, psycopg2.DatabaseError) as e:
            globalutils.show_stack_trace(str(e))
            sentlog.append(f"Error! {str(e)}")
        finally:
            self.close_connection()

from globals import globalvars
from globals import globalutils
from globals import sentop_log
import re

# Clean and remove stop words for topic modeling: LDA. 
def topic_modeling_clean_stop(data_list, stop_words):

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
            print(f"&#8226; WARNING! Cleaning resulted in empty text. Using orig text: {cleaned_sentence}.")
        cleaned.append(cleaned_sentence)

    return cleaned


# JSON to Postgres: Escape single quotes due to postresql
def clean_postgres_json(text):
    text = text.replace("'", "''")
    return text


# Clean non-JSON text. 
def clean(text):
    if not text:
        return text
    text = text.replace('"', '')
    text = text.replace("'", '')
    text = text.replace('\r','')
    text = text.replace('\n','')
    text = text.replace('\t','')
    text = text.replace('_x000d_','') # Excel line feed
    return text


def remove_invalid_datapoints(row_id_list, data_list, all_stop_words):

    sentlog = sentop_log.SentopLog()
    ignored_one_stopword = 0
    ignored_all_stopwords = 0
    ignored_no_alpha = 0
    ignored_bad_num_words = 0
    ignored_na = 0
    ignored_none = 0
    text_checker = globalutils.TextChecker(all_stop_words)

    new_row_id_list = []
    new_data_list = []

    sentlog.info(f"Document errors|", html_tag='keyval')
    sentlog.info(f"<pre>", html_tag='other')

    for i in range (len(data_list)):
        id = row_id_list[i]
        text = data_list[i]

        # Preprocess text to see if it should be removed from consideration
        text_preproc = text.lower()
        text_preproc = re.sub(r'[^\w\s]', ' ', text_preproc)
        text_preproc.strip()
        #print(f"text_preproc: {text_preproc}")

        # --------------------------- CHECK TEXT -------------------------------

        # Check for blank or NA value. NOTE: Python can't detect the string
        # literal 'none' (it's a reserved literal), so we cannot check for it here.
        if not text_preproc or text_preproc == 'na' or text_preproc == 'n/a' or text_preproc == 'not applicable':
            sentlog.info(f"- {id}: '{text}' -- ERROR! 'NA', 'N/A', or 'Not Applicable' found.", html_tag='p')
            ignored_na = ignored_na + 1
            continue

        # Check if text contains at least one alphabetic character
        found_letter = any(c.isalpha() for c in text_preproc)
        if not found_letter:
            sentlog.info(f"- {id}: '{text}' -- ERROR! No alphabetic characters found.", html_tag='p')
            ignored_no_alpha = ignored_no_alpha + 1
            continue

        # Check if valid number of words in text is less than minimum allowed
        good_num = text_checker.check_num_words(text_preproc)
        if not good_num:
            sentlog.info(f"- {id}: '{text}' -- ERROR! Number of valid (alphabetic) words less than min allowed after preprocessing.", html_tag='p')
            ignored_bad_num_words = ignored_bad_num_words + 1
            continue

        # Check if entire text is a stop word (including user-defined stop word)
        new_text = text_checker.check_entire_text(text_preproc)
        if not new_text:
            sentlog.info(f"- {id}: '{text}' -- ERROR! Text matches a stop word.", html_tag='p')
            ignored_one_stopword = ignored_one_stopword + 1
            continue

        # Check if text comprises all stop words 
        new_text = text_checker.check_each_word(text_preproc)
        if not new_text:
            sentlog.info(f"- {id}: '{text}' -- ERROR! Text comprises all stop words.", html_tag='p')
            ignored_all_stopwords = ignored_all_stopwords + 1
            continue

        # --------------------------- CLEAN TEXT -------------------------------

        #print(f"Text: {text}")
        # Trim if number of words in text is greater than max allowed
        trimmed_text = text_checker.trim_text(text)
        #print(f"trimmed_text: {trimmed_text}")

        # Clean data
        cleaned_text = clean(trimmed_text)
        #print(f"cleaned_text: {cleaned_text}")

        # Check if text comprises all stop words 
        if not cleaned_text:
            sentlog.info(f"- {id}: '{text}' -- ERROR! Cleaned text removed all words.", html_tag='p')
            ignored_none = ignored_none + 1
            continue

        # Add to new data list
        new_row_id_list.append(row_id_list[i])
        new_data_list.append(cleaned_text)

    sentlog.info(f"</pre>", html_tag='other')
    sentlog.info(f"Documents removed|", html_tag='keyval')
    sentlog.info(f"<pre>", html_tag='other')

    if ignored_none > 0:
        sentlog.info(f"- WARNING: {ignored_none} docs removed due to cleaned text = None.", html_tag='p')
    else:
        sentlog.info(f"- {ignored_none} docs removed due to cleaned text = None.", html_tag='p')

    if ignored_na > 0:
        sentlog.info(f"- WARNING: {ignored_na} docs removed due to 'NA' or 'N/A' values.", html_tag='p')
    else:
        sentlog.info(f"- {ignored_na} docs removed due to blank or NA values.", html_tag='p')
        
    if ignored_one_stopword > 0:
        sentlog.info(f"- WARNING: {ignored_one_stopword} docs removed due to text comprising a single stop word/phrase.", html_tag='p')
    else:
        sentlog.info(f"- {ignored_one_stopword} docs removed due to text comprising a single stop word/phrase.", html_tag='p')

    if ignored_all_stopwords > 0:
        sentlog.info(f"- WARNING: {ignored_all_stopwords} docs removed due to text comprising all stop words.", html_tag='p')
    else:
        sentlog.info(f"- {ignored_all_stopwords} docs removed due to text comprising all stop words.", html_tag='p')

    if ignored_no_alpha > 0:
        sentlog.info(f"- WARNING: {ignored_no_alpha} docs removed due to text containing only non-alphabetic characters.", html_tag='p')
    else:
        sentlog.info(f"- {ignored_no_alpha} docs removed due to text containing only non-alphabetic characters.", html_tag='p')
    
    if ignored_bad_num_words > 0:
        sentlog.info(f"- WARNING: {ignored_bad_num_words} docs removed due to text having number of words less than min allowed.", html_tag='p')
    else:
        sentlog.info(f"- {ignored_bad_num_words} docs removed due to text having number of words less than min allowed ({globalvars.MIN_DOC_WORDS}).", html_tag='p')
        
    num_docs_ignored = ignored_none + ignored_na + ignored_one_stopword + ignored_all_stopwords + ignored_no_alpha + ignored_bad_num_words
    percent_docs_ignored =  num_docs_ignored / len(data_list)
    perc = str(round(percent_docs_ignored*100, 2))
    if num_docs_ignored > 0:
        sentlog.info(f"- WARNING: {num_docs_ignored} ({perc}%) total non-blank docs removed.", html_tag='p')
    else:
        sentlog.info(f"- {num_docs_ignored} total docs ignored.") 

    total_docs_to_analyze = len(data_list) - num_docs_ignored
    total_perc_ignored = total_docs_to_analyze / len(data_list)
    total_perc_ignored = str(round(total_perc_ignored*100, 2))
    sentlog.info(f"</pre>", html_tag='other')
    sentlog.info(f"Documents analyzed|{total_docs_to_analyze} out of {len(data_list)} documents ({total_perc_ignored}%).<br>", html_tag='keyval')

    return new_row_id_list, new_data_list, None



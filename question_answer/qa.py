from transformers import pipeline
from globals import globalutils
from globals import sentop_log


#from transformers import AutoTokenizer, AutoModelForQuestionAnswering

# tokenizer1 = AutoTokenizer.from_pretrained("distilbert-base-cased-distilled-squad")
# model1 = AutoModelForQuestionAnswering.from_pretrained("distilbert-base-cased-distilled-squad")
#
# tokenizer3 = AutoTokenizer.from_pretrained("valhalla/longformer-base-4096-finetuned-squadv1")
# model3 = AutoModelForQuestionAnswering.from_pretrained("valhalla/longformer-base-4096-finetuned-squadv1")
#
# tokenizer4 = AutoTokenizer.from_pretrained("distilbert-base-uncased-distilled-squad")
# model4 = AutoModelForQuestionAnswering.from_pretrained("distilbert-base-uncased-distilled-squad")
nlp1 = pipeline("question-answering", model="deepset/roberta-base-squad2",
                       tokenizer="deepset/roberta-base-squad2")
nlp2 = pipeline("question-answering", model="bert-large-uncased-whole-word-masking-finetuned-squad",
                       tokenizer="bert-large-uncased-whole-word-masking-finetuned-squad")
nlp3 = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad",
                       tokenizer="distilbert-base-uncased-distilled-squad")

# def run_model1(question, context):
#     inputs = tokenizer1.encode_plus(question, context, add_special_tokens=True, return_tensors="pt")
#     input_ids = inputs["input_ids"].tolist()[0]
#
#     text_tokens = tokenizer1.convert_ids_to_tokens(input_ids)
#     answer_start_scores, answer_end_scores = model1(**inputs)
#
#     answer_start = torch.argmax(
#         answer_start_scores)  # Get the most likely beginning of answer with the argmax of the score
#     answer_end = torch.argmax(answer_end_scores) + 1  # Get the most likely end of answer with the argmax of the score
#
#     answer = tokenizer1.convert_tokens_to_string(tokenizer1.convert_ids_to_tokens(input_ids[answer_start:answer_end]))
#     return answer
#
# def run_model3(question, context):
#     inputs = tokenizer3.encode_plus(question, context, add_special_tokens=True, return_tensors="pt")
#     input_ids = inputs["input_ids"].tolist()[0]
#
#     text_tokens = tokenizer3.convert_ids_to_tokens(input_ids)
#     answer_start_scores, answer_end_scores = model3(**inputs)
#
#     answer_start = torch.argmax(
#         answer_start_scores)  # Get the most likely beginning of answer with the argmax of the score
#     answer_end = torch.argmax(answer_end_scores) + 1  # Get the most likely end of answer with the argmax of the score
#
#     answer = tokenizer3.convert_tokens_to_string(tokenizer3.convert_ids_to_tokens(input_ids[answer_start:answer_end]))
#     return answer
#
# def run_model4(question, context):
#     inputs = tokenizer4.encode_plus(question, context, add_special_tokens=True, return_tensors="pt")
#     input_ids = inputs["input_ids"].tolist()[0]
#
#     text_tokens = tokenizer4.convert_ids_to_tokens(input_ids)
#     answer_start_scores, answer_end_scores = model4(**inputs)
#
#     answer_start = torch.argmax(
#         answer_start_scores)  # Get the most likely beginning of answer with the argmax of the score
#     answer_end = torch.argmax(answer_end_scores) + 1  # Get the most likely end of answer with the argmax of the score
#
#     answer = tokenizer4.convert_tokens_to_string(tokenizer4.convert_ids_to_tokens(input_ids[answer_start:answer_end]))
#     return answer

def is_valid(answer):
    if not answer:
        return False
    elif "<s>" in answer or "</s>" in answer:
        return False
    else:
        return True

def run_qa(m, question, para):
    if m == 'model1':
        return nlp1(question=question, context=para)
    elif m == 'model2':
        return nlp2(question=question, context=para)
    else:
        return nlp3(question=question, context=para)

class Result:
    def __init__(self, answer, score):
        self.answer = answer
        self.score = score

def assess(question, paragraphs):
    answers = []
    for para in paragraphs:
        #print("Section para: ", para)
        result = run_qa("model1", question, para)
        if is_valid(result.get("answer")):
            r = Result(result.get("answer"), result.get("score"))
            #print(r.answer, r.score)
            if not any(r.answer == x.answer for x in answers):
                answers.append(r)
        else:
            result = run_qa("model2", question, para)
            if is_valid(result.get("answer")):
                r = Result(result.get("answer"), result.get("score"))
                #print(r.answer, r.score)
                if not any(r.answer == x.answer for x in answers):
                    answers.append(r)
            else:
                result = run_qa("model3", question, para)
                if is_valid(result.get("answer")):
                    r = Result(result.get("answer"), result.get("score"))
                    #print(r.answer, r.score)
                    if not any(r.answer == x.answer for x in answers):
                        answers.append(r)
    # To return a new list, use the sorted() built-in function...
    answers.sort(key=lambda x: x.score, reverse=True)
    return answers

'''
def assess(docs):
    qa = EasyQuestionAnswering()

    sentlog = sentop_log.SentopLog()
    sentlog.info(f"Question-Answer", html_tag='h2')
    #sentlog.info(f"Model|<a href=\"https://huggingface.co/{model_name}\" target=\"_blank\">{model_name}</a>", html_tag='keyval')

    i = 0
    for doc in docs:
        print("doc: ", doc)
        best_answer, best_n_answers = qa.predict_qa(query="What is good?", context=doc, n_best_size=1, mini_batch_size=1, model_name_or_path="distilbert-base-uncased-distilled-squad")
        
        if best_answer:
            print(f"QA Answer: {best_answer}")
        else:
            print("QA No answer")

        #if i % 100 == 0:
        #    print("Processing 3-class: ", i)
        i = i + 1

    return globalutils.Sentiments("class3", f"3-Class ({model_name})", model_name, "polarity", sentiments)
'''
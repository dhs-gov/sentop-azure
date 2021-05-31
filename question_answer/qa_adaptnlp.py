from adaptnlp import EasyQuestionAnswering 
from globals import globalutils

def assess(docs):
    query = "What is the meaning of life?"
    context = "Machine Learning is the meaning of life."
    top_n = 1

    ## Load the QA module and run inference on results 
    qa = EasyQuestionAnswering()


    sentlog = globalutils.SentopLog()
    sentlog.append(f"<h2>Question-Answer</h2>")
    #sentlog.append(f"<b>Model:</b> <a href=\"https://huggingface.co/{model_name}\" target=\"_blank\">{model_name}</a><br>")

    i = 0
    for doc in docs:
        print("doc: ", doc)
        best_answer, best_n_answers = qa.predict_qa(query="What is good?", context=doc, n_best_size=top_n, mini_batch_size=1, model_name_or_path="distilbert-base-uncased-distilled-squad")
        
        if best_answer:
            print(f"QA Answer: {best_answer}")
        else:
            print("QA No answer")

        #if i % 100 == 0:
        #    print("Processing 3-class: ", i)
        i = i + 1

    return None

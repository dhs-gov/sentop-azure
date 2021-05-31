import logging
import jsonpickle
import azure.functions as func
import azure.durable_functions as df
from data_util import data_extractor
from data_util import data_cleaner
from database import postgres
from globals import globalutils
from datetime import datetime
from dateutil import tz
import sentop_config as config

class DataIn:
    def __init__(self, kms_id, sentop_id, row_id_list, data_list, all_stop_words, annotation):
        #print(f"Creating DataIn with SENTOP ID: {sentop_id}")
        self.kms_id = kms_id
        self.sentop_id = sentop_id
        self.row_id_list = row_id_list  
        self.data_list = data_list
        self.all_stop_words = all_stop_words
        self.annotation = annotation
            

# Returns SENTOP ID based on current timestamp.
def get_sentop_id():
    import datetime
    milliseconds_since_epoch = datetime.datetime.now().timestamp() * 1000
    return str(int(milliseconds_since_epoch))


# Returns id, file_url, is_test, error
def check_query_params(req):
    sentlog = globalutils.SentopLog()

    valid_endpoint_namesnames = ['sentop', 'sentop-test']
    endpoint_name = req.route_params.get('functionName')
    if endpoint_name not in valid_endpoint_namesnames:
        return None, None, False, "Invalid endpoint name."
    elif endpoint_name == 'sentop-test':
        test_requested = True
        return None, None, test_requested, False

    kms_id = req.params.get('id')

    if not kms_id:
        return None, None, False, "Query parameter 'id' not received."
    elif kms_id.startswith('http') or kms_id.startswith('file'):
        #sentlog.append(f"- Received file URL: {kms_id}")
        # Azure replaces '%20' with spaces, so re-add '%20' since this is
        # required for Windows file URLs.
        file_url = kms_id.replace(" ", "%20")
        sentop_id = get_sentop_id()
        return "url" + sentop_id, file_url, False, None
    else:
        sentop_id = get_sentop_id()
        return "kms" + sentop_id, kms_id, False, None


# ================================== M A I N ===================================

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:

    sentlog = globalutils.SentopLog()
    sentlog.clear()

    print(">>>>>>>>>>>>>>>>>> S T A R T >>>>>>>>>>>>>>>>")
    sentlog.append("<br><br><div style=\"line-height: 110%; text-align: center; font-size: 30px; font-weight: bold;\">SENTOP</div>\n")
    sentlog.append("<div style=\"line-height: 160%; text-align: center; font-size: 18px;\"><a href=\"https://github.com/dhs-gov/sentop\" target=\"_blank\">github.com/dhs-gov/sentop</a></div>\n")
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')
    utc = datetime.utcnow()
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    sentlog.append(f"<div style=\"text-align: center; font-size: 16px;\">{central.strftime('%B %d %Y - %H:%M:%S')} EST</div><br>\n")

    # ---------------------------- SET LOGGING ---------------------------------

    logging.basicConfig(force=True, format='%(asctime)s %(levelname)-4s [%(filename)s:%(lineno)d] %(message)s', 
        datefmt='%Y-%m-%d:%H:%M:%S', level=logging.INFO)

    # Set the logging level for all azure-* libraries
    #logger = logging.getLogger('azure')
    #logger.setLevel(print)

   # -------------------- DELETE EXISTING RUN INSTANCES -----------------------

    # Azure Durable Functions retain instances of runs that do not complete
    # successfully. These instances are queued and re-run at a later time.
    # This re-running of previous instances could lead to unexpected execution
    # of previous runs. To check if previous run instances are queued by Azure,
    # view the storage account by using the Azure Storage Explorer. The
    # following attempts to check for previous runs queued in storage and
    # remove them. Note that this block of code cannot be moved to a function
    # because the 'awaits' keyword must be within scope of the async function.
    # Delete any existing (old) run instances, otherwise previous runs will
    # 'replay'.

    client = df.DurableOrchestrationClient(starter)
    instances = await client.get_status_all()
    # sentlog.append("Previous run instances found: ", len(instances))
    for instance in instances:
        old_instance_id = instance.instance_id
        # Terminate previous run instances
        status = await client.get_status(old_instance_id)
        status_str = str(status.runtime_status)
        #sentlog.append("- Instance Status: ", status_str)
        if status_str == 'OrchestrationRuntimeStatus.Completed':
            purge_results = await client.purge_instance_history(old_instance_id)
            # sentlog.append("Purged instance: ", purge_results)
        else:
            #sentlog.append("Instance NOT COMPLETED-TERMINATING!: ", old_instance_id)
            await client.terminate(old_instance_id, "Trying to terminate")
            purge_results = await client.purge_instance_history(old_instance_id)
            # sentlog.append("Terminated old instance: ", purge_results)
            #sentlog.append("Terminating old instances.")

    # Make sure old instances are deleted
    instances = await client.get_status_all()
    for instance in instances:
        if instance:
            sentlog.append(f"<div style=\"font-weight: bold; color: #e97e16; \">&#8226; WARNING! Old instance still alive.</div><br>")


   # -------------------------- CHECK QUERY PARAMS -----------------------------

    sentlog.append("<br><br>")
    sentlog.append("<h1>Request</h1>\n")

    sentop_id, kms_id, is_test, error = check_query_params(req)
    if error:
        sentlog.append(f"<div style=\"font-weight: bold; color: red; \">&#8226; {error}</div><br>")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse(error, status_code=400)
    if is_test:
        sentlog.append("Test request successful.")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse("SENTOP test successful.", status_code=200)


    #if kms_id.startswith('http'):
    #    kms_id = f"<a href=\\\"{kms_id}\\\" target=\\\"_blank\\\">{kms_id}</a>"

    sentlog.append(f"<b>&#8226; KMS ID:</b> {kms_id}<br>")
    sentlog.append(f"<b>&#8226; SENTOP ID:</b> {sentop_id}")

   # ---------------------- SAVE REQUEST DATA TO DB ----------------------------

    db = postgres.Database()
    error = db.add_submission(sentop_id, kms_id)
    if error:
        sentlog.append(f"<div style=\"font-weight: bold; color: red; \">&#8226; {error}</div><br>")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse(error, status_code=400)

   # ------------------------ CONVERT INCOMING DATA ----------------------------

    sentlog.append("<h1>Data</h1>\n")
    row_id_list, data_list, user_stop_words, annotation, error = data_extractor.get_data(req, sentop_id, kms_id)

    if error:
        sentlog.append(f"<div style=\"font-weight: bold; color: red; \">&#8226; ERROR! Could not find file. Aborting.</div><br>")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse(error, status_code=400)
    elif not data_list:
        sentlog.append(f"<div style=\"color: red; \"ERROR! Could not find JSON or file data.</div><br>")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse("Error retrieving JSON or file data.", status_code=400)
    
    sentlog.append(f"<b>&#8226; Non-blank documents:</b> {len(data_list)}<br>")

    if annotation:
        sentlog.append(f"<b>&#8226; Annotation: </b> {annotation}<br>")
        annotation_error = db.add_annotation(sentop_id, annotation)
        if annotation_error:
            sentlog.append(f"<div style=\"font-weight: bold; color: #e97e16; \">&#8226; WARNING! Could not update annotation in database: {annotation_error}.</div><br>")

    if len(data_list) != len(row_id_list):
        sentlog.append("<div style=\"color: red; \">ERROR! Number of rows does not match number of documents.</div><br>")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse("ERROR! Number of rows does not match number of documents.", status_code=400)

    if not user_stop_words:
        sentlog.append(f"<div style=\"font-weight: bold; color: #e97e16; \">&#8226; WARNING! No user stop words found.</div>")

        
    #for i in range(len(row_id_list)):
    #    sentlog.append(f"Got: {row_id_list[i]} = {data_list[i]}")

   # ---------------------- GET ALL STOP WORDS --------------------------

    all_stop_words = globalutils.get_frozen_stopwords(user_stop_words)

   # ---------------------- REMOVE INVALID DATAPOINTS --------------------------

    # Apply stopwords and additional checks to remove invalid documents (rows).
    row_id_list, data_list, error = data_cleaner.remove_invalid_datapoints(row_id_list, data_list, all_stop_words)

    if len(data_list) != len(row_id_list):
        sentlog.append("ERROR! Number of rows does not match number of documents.")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse("ERROR! Number of rows does not match number of documents.", status_code=400)


   # ------------------ CREATE JSON DATA FOR AZURE ACTIVITY --------------------

    #sentlog.append("Data in: ", data_list)
    data_list_obj = DataIn(kms_id, sentop_id, row_id_list, data_list, all_stop_words, annotation)

    # Since Azure requires that we pass an object that is JSON
    # serializable, we have to convert all data to a JSON object.
    json_obj = jsonpickle.encode(data_list_obj, unpicklable=True)
    

    # ------------------------ CREATE NEW INSTANCE -----------------------------

    # Note that "functionName" gets automatically resolved to req.method function name
    # (e.g., 'sentop').

    #sentlog.append("Starting orchestration")
    #sentlog.append("Starting SENTOP analysis.")

    instance_id = await client.start_new(req.route_params["functionName"], None, json_obj)

    #sentlog.append(f"Started orchestration with ID = '{instance_id}'.")

    # -------------------------- RETURN RESPONSE -------------------------------

    response = client.create_check_status_response(req, instance_id)
    #sentlog.append("Returned Azure URL links.")

    return response

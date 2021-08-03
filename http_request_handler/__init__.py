import logging
import jsonpickle
import azure.functions as func
import azure.durable_functions as df
from data_util import data_extractor
from data_util import data_cleaner
from database import postgres
from globals import globalutils
from globals import sentop_log
from datetime import datetime
from dateutil import tz
import sentop_config as config
from globals import sentop_log


class DataIn:
    def __init__(self, kms_id, sentop_id, row_id_list, data_list, all_stop_words, annotation):
        #print(f"Creating DataIn with SENTOP ID: {sentop_id}")
        self.kms_id = kms_id
        self.sentop_id = sentop_id
        self.row_id_list = row_id_list  
        self.data_list = data_list
        self.all_stop_words = all_stop_words
        self.annotation = annotation
            

# Returns SENTOP ID generated from current timestamp.
def get_sentop_id():
    import datetime
    milliseconds_since_epoch = datetime.datetime.now().timestamp() * 1000
    return str(int(milliseconds_since_epoch))


# Returns id, file_url, is_test, error
def check_query_params(req):
    sentlog = sentop_log.SentopLog()

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

    sentlog = sentop_log.SentopLog()
    sentlog.reset()
    sentlog.set_level('DEBUG')

    # ---------------------------- SET LOGGING ---------------------------------

    logging.basicConfig(
        force=True, 
        format='%(asctime)s %(levelname)-4s [%(filename)s:%(lineno)d] %(message)s', 
        datefmt='%Y-%m-%d:%H:%M:%S', 
        level=logging.INFO)

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
            sentlog.warn(f"Old Azure instance still alive.")

   # -------------------------- CHECK QUERY PARAMS -----------------------------

    sentlog.h1("Request")

    sentop_id, kms_id, is_test, error = check_query_params(req)
    if error:
        sentlog.error(f"{error}")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse(error, status_code=400)
    if is_test:
        sentlog.info("Test request successful.", html_tag='p')
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse("SENTOP test successful.", status_code=200)

    sentlog.info(f"KMS ID|{kms_id}", html_tag='keyval')
    sentlog.info(f"SENTOP ID|{sentop_id}", html_tag='keyval')

   # ---------------------- SAVE REQUEST DATA TO DB ----------------------------

    db = postgres.Database()
    error = db.add_submission(sentop_id, kms_id)
    if error:
        sentlog.error(f"{error}")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse(error, status_code=400)

   # ------------------------ CONVERT INCOMING DATA ----------------------------

    sentlog.info("Data", html_tag='h1')
    row_id_list, data_list, user_stop_words, annotation, error = data_extractor.get_data(req, sentop_id, kms_id)

    if error:
        sentlog.error(f"Could not find file. Aborting.")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse(error, status_code=400)
    elif not data_list:
        sentlog.error(f"Could not find JSON or file data.")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse("Error retrieving JSON or file data.", status_code=400)
    
    sentlog.info(f"Non-blank documents|{len(data_list)}", html_tag='keyval')

    if annotation:
        sentlog.info(f"Annotation|{annotation}", html_tag='keyval')
        annotation_error = db.add_annotation(sentop_id, annotation)
        if annotation_error:
            sentlog.warn(f"Could not update annotation in database: {annotation_error}.")

    if len(data_list) != len(row_id_list):
        sentlog.error("Number of rows does not match number of documents.")
        sentlog.write(sentop_id, config.data_dir_path.get("output"))
        return func.HttpResponse("ERROR! Number of rows does not match number of documents.", status_code=400)

    if not user_stop_words:
        sentlog.warn(f"No user stop words found.")

   # ---------------------- GET ALL STOP WORDS --------------------------

    all_stop_words = globalutils.get_frozen_stopwords(user_stop_words)

   # ---------------------- REMOVE INVALID DATAPOINTS --------------------------

    # Apply stopwords and additional checks to remove invalid documents (rows).
    row_id_list, data_list, error = data_cleaner.remove_invalid_datapoints(row_id_list, data_list, all_stop_words)

    if len(data_list) != len(row_id_list):
        sentlog.error("Number of rows does not match number of documents.")
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
    instance_id = await client.start_new(req.route_params["functionName"], None, json_obj)

    # -------------------------- RETURN RESPONSE -------------------------------

    response = client.create_check_status_response(req, instance_id)
    #sentlog.append("Returned Azure URL links.")

    return response

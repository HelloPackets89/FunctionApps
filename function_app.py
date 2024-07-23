import os
import pyodbc
from azure.storage.blob import BlobClient
import datetime
from openai import AsyncOpenAI
import logging
import azure.functions as func
from azure.core.exceptions import ResourceNotFoundError

app = func.FunctionApp()

@app.timer_trigger(schedule="0 45 16 * * 5", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
async def timer_trigger1(myTimer: func.TimerRequest) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        # Define my connection string, error checking if it's not able to find the key
        blobkey = os.environ.get('BLOB_KEY')
        if not blobkey:
            logging.error("BLOB_KEY environment variable not set")
            return
        #Define the filenames for what I want to access
        lastweek = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y%m%d")
        lastweektxt = f"visitors{lastweek}.txt"
        thisweek = datetime.date.today().strftime("%Y%m%d")
        thisweektxt = f"visitors{thisweek}.txt"
        # Setup the blob connections for this week and last week
        blob_lastweek = BlobClient.from_connection_string(blobkey, "results", lastweektxt)
        blob_thisweek = BlobClient.from_connection_string(blobkey, "results", thisweektxt)
        # Convert the txt inside the files to something that's useable
        try:
            data_lastweek = blob_lastweek.download_blob().readall().decode('utf-8')
        except ResourceNotFoundError:
            logging.error("Could not find blob 'visitors20240715.txt' in container 'results'")
            return
        try:
            data_thisweek = blob_thisweek.download_blob().readall().decode('utf-8')
        except ResourceNotFoundError:
            logging.error("Could not find blob 'visitors20240722.txt' in container 'results'")
            return
        # Log the contents for test purposes. Set it as warning so it stands out. 
        logging.warning(f"The text contained in last week is {data_lastweek}")
        logging.warning(f"The text contained in this week is {data_thisweek}")

    except Exception as e:
        # Log any exceptions that occur
        logging.error(f"An error occurred: {e}")
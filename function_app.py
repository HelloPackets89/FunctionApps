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
    logging.getLogger().setLevel(logging.INFO)
    logging.info('Python timer trigger function started')

    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        # Define my connection string, error checking if it's not able to find the key
        blobkey = os.environ.get('BLOB_KEY')
        if not blobkey:
            logging.error("BLOB_KEY environment variable not set")
            return

        logging.info("Setting key")
        
        # Setup the blob connections for this week and last week
        blob_lastweek = BlobClient.from_connection_string(blobkey, "results", "visitors20240715.txt")
        blob_thisweek = BlobClient.from_connection_string(blobkey, "results", "visitors20240722.txt")
        logging.info("Setting connections")

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

        # Log the contents for test purposes
        logging.info("Attempting to output the container text...")
        logging.info(f"The text contained in last week is {data_lastweek}")
        logging.info(f"The text contained in this week is {data_thisweek}")

        # Add your main function logic here

    except Exception as e:
        # Log any exceptions that occur
        logging.error(f"An error occurred: {e}")
        raise  # Re-raise the exception to mark the function as failed

    logging.info('Python timer trigger function completed')
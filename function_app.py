import os
import pyodbc
from azure.storage.blob import BlobClient
import datetime
from openai import AsyncOpenAI
import logging
import azure.functions as func
from azure.core.exceptions import ResourceNotFoundError

app = func.FunctionApp()

@app.timer_trigger(schedule="0 45 16 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
async def analyse_visits(myTimer: func.TimerRequest) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        # Define my connection string, error checking if it's not able to find the key
        blobkey = os.environ.get('BLOB_KEY')
        if not blobkey:
            logging.error("BLOB_KEY environment variable not set")
            return
        #Define the filenames for what I want to access
        lastweek = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d")
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
            logging.error(f"Could not find blob {lastweektxt} in container 'results'")
            return
        try:
            data_thisweek = blob_thisweek.download_blob().readall().decode('utf-8')
        except ResourceNotFoundError:
            logging.error(f"Could not find blob {thisweektxt} in container 'results'")
            return
        #Define the prompt I want to be using that includes a reference to the data contained in the text files.
        prompt = f'''I have two sets of results that display the Public IP address of my visitors and how many times they've visited. 
                    I want to compare results A with results B. Please advise me of the following:
                    1. Any new visitors and how many visits they have
                    2. Any changes in visit counts
                    3. Any other interesting trends that you've noticed.
                    
                    Result A:
                    {data_lastweek}
                    Result B:
                    {data_thisweek}'''

        client = AsyncOpenAI(
         api_key=os.environ['OPENAI_API_KEY'],  # Reference the API key in my function app environment
        )
        response = await client.chat.completions.create(model="gpt-3.5-turbo",
                                                          messages=[{"role": "user", "content": prompt}])
        # Log the content of the first message in the completion choices
        logging.warning(response.choices[0].message.content)

    except Exception as e:
        # Log any exceptions that occur
        logging.error(f"An error occurred: {e}")
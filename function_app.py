import os
import pyodbc
from azure.storage.blob import BlobClient
import datetime
from openai import AsyncOpenAI
import logging
import azure.functions as func



app = func.FunctionApp()

@app.timer_trigger(schedule="0 45 16 * * 5", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
async def timer_trigger1(myTimer: func.TimerRequest) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

            #Define my connection string
            blobkey =os.environ['BLOB_KEY']
            #Setup the blob connections for this week and last week
            blob_lastweek = BlobClient.from_connection_string(blobkey, "results", "visitors20240715.txt")
            blob_thisweek = BlobClient.from_connection_string(blobkey, "results", "visitors20240722.txt")
            #Convert the txt inside the files to something thats useable
            data_lastweek = blob_lastweek.download_blob().readall().decode('utf-8')
            data_thisweek = blob_thisweek.download_blob().readall().decode('utf-8')
            #Log the contents for test purposes
            logging.info(f"The text contained in last week is {data_lastweek}")
            logging.info(f"The text contained in this week is {data_thisweek}")

    except Exception as e:
            # Log any exceptions that occur
            logging.error(f"An error occurred: {e}")

    #     prompt = '''I have two sets of results that display the Public IP address of my visitors and how many times they've visited. 
    #                 I want to compare results A with results B. Please advise me of the following:
    #                 1. Any new visitors and how many visits they have
    #                 2. Any changes in visit counts
    #                 3. Any other interesting trends that you've noticed.
                    
    #                 Result A:
    #                 ('1.1.1.1', 24)
    #                 ('2.2.2.2', 1)
    #                 ('61.123.456.21', 43)
    #                 ('1.2.3.4', 27)
    #                 ('51.123.456.21', 23)

    #                 Result B:
    #                 ('1.1.1.1', 30)
    #                 ('2.2.2.2', 1)
    #                 ('61.123.456.21', 50)
    #                 ('1.2.3.4', 30)
    #                 ('51.123.456.21', 30)
    #                 ('3.3.3.3', 10)'''

    #     client = AsyncOpenAI(
    #      api_key=os.environ['OPENAI_API_KEY'],  # Reference the API key in my function app environment
    #     )
    #     response = await client.chat.completions.create(model="gpt-3.5-turbo",
    #                                                       messages=[{"role": "user", "content": prompt}])
    #     # Log the content of the first message in the completion choices
    #     logging.info(response.choices[0].message.content)


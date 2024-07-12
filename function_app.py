import os
import pyodbc
from azure.storage.blob import BlobServiceClient
import datetime
import openai
import logging
import azure.functions as func

app = func.FunctionApp()

@app.timer_trigger(schedule="0 45 16 * * 5", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger1(myTimer: func.TimerRequest) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        client = openai.ChatCompletion()

        completion = client.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
            {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
            ]
        )
        # Log the content of the first message in the completion choices
        logging.info(completion['choices'][0]['message']['content'])

    except Exception as e:
        # Log any exceptions that occur
        logging.error(f"An error occurred: {e}")
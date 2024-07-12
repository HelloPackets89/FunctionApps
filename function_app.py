

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
def timer_trigger2(myTimer: func.TimerRequest) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        client = openai()

        completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
            {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
            ]
        )
        # Print the content of the first message in the completion choices
        print(completion['choices'][0]['message']['content'])

    except Exception as e:
        # Print any exceptions that occur
        print(f"An error occurred: {e}")
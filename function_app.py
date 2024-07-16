import os
import pyodbc
from azure.storage.blob import BlobServiceClient
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

        prompt = '''brandon is awesome
                    and a cool guy
                    tell me 5 reasons why brandon is so awesome please'''

        client = AsyncOpenAI(
         api_key=os.environ['OPENAI_API_KEY'],  # Reference the API key in my function app environment
        )
        response = await client.chat.completions.create(model="gpt-3.5-turbo",
                                                          messages=[{"role": "user", "content": prompt}])
        # Log the content of the first message in the completion choices
        logging.info(response.choices[0].message.content)

    except Exception as e:
        # Log any exceptions that occur
        logging.error(f"An error occurred: {e}")
import os
from openai import AzureOpenAI
import logging
import azure.functions as func
from azure.communication.email import EmailClient

app = func.FunctionApp()

@app.timer_trigger(schedule="0 45 16 * * 5", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
async def timer_trigger1(myTimer: func.TimerRequest) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        client = AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = "2024-02-01",
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        prompt = f'''Bill I need you to explain the following:
                            Why did you name Microsoft Microsoft and not Megasoft?'''

        response = client.chat.completions.create(
            model="BrandonAI", # model = "deployment_name".
            messages=[{"role": "user", "content": prompt}])

        #Define the prompt I want to be using that includes a reference to the data contained in the text files.

        # Log the content of the first message in the completion choices
        promptresponse = (response.choices[0].message.content)
        logging.warning(promptresponse)

        #Email the results to me
        emailkey = os.environ.get('EMAIL_KEY')
        client = EmailClient.from_connection_string(emailkey)

        message = {
            "senderAddress": "visitormonitor@brandedkai.net",
            "recipients":  {
                "to": [{"address": "brandon@allmark.me" }],
            },
            "content": {
                "subject": f"Visitors analysis of today",
                "plainText": f"{promptresponse}",
            }
        }

        poller = client.begin_send(message)
        poller.result()

    except Exception as e:
        # Log any exceptions that occur
        logging.error(f"An error occurred: {e}")

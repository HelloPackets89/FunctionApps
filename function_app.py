import os
import pyodbc
from azure.storage.blob import BlobClient, BlobServiceClient
import datetime
from openai import AsyncOpenAI
import logging
import azure.functions as func
from azure.core.exceptions import ResourceNotFoundError
from azure.communication.email import EmailClient

app = func.FunctionApp()

#The timer trigger decorator is what defines when and how often my function is running.
#The retry decorator defines how often my app will try again if it fails for whatever reason. 
#Both of these decorators have the "power" to make my function app run again 
@app.timer_trigger(schedule="0 45 8 * * *", arg_name="myTimer", run_on_startup=False,use_monitor=False) 
@app.retry(strategy="fixed_delay", max_retry_count="5",delay_interval="00:00:01")
def dbqueryandsave(myTimer: func.TimerRequest, context: func.Context) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        # Get the connection strings from the environmental settings
        # This connects to my blob storage and my SQL DB
        conn_str = os.getenv('SQLDB_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(os.getenv('AzureWebJobsStorage'))
        logging.info('Attempting connection')
        # Create a new connection
        conn = pyodbc.connect(conn_str)

        # Create a cursor from the connection. The cursor is what interacts with my database. 
        # The cursor can be used to "move around" the database and fetch individual rows. I'm just printing everything. 
        cur = conn.cursor()

        # Query my database and get data from the ResumeVisitors table
        logging.warning('Attempting query..')
        cur.execute("SELECT TOP (1000) * FROM ResumeVisitors")

        # Set the filename I plan to use for my results
        # putting "f" infront of strings means it parses the variables inside the string, instead of just putting the name of the variable. 
        today = datetime.date.today().strftime("%Y%m%d")
        filename = f"visitors{today}.txt"
        blob_client = blob_service_client.get_blob_client("results", filename)

        # Fetch all the results of the query and add it to my file
        rows = cur.fetchall()
        all_rows = []
        #For each row found in the query results, combine them into one string. 
        for row in rows:
            all_rows.append(str(row))

        all_rows_str = '\n'.join(all_rows)
        logging.warning(all_rows_str)
        # Upload all the results to the storage account using the predefined filename. 
        # If this file already exists, the attempt to upload will fail. This is intentional. 
        blob_client.upload_blob(all_rows_str)

    # Error logging - this section provides more verbose errors if the function app fails for whatever reason.\
    # \n refers to printing a new line
    # this error logging was ripped from microsoft learn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0] if len(ex.args) > 0 else None
        logging.error(f'Database error occurred:\nSQLState: {sqlstate}\nError: {ex}')
        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    except Exception as e:
        logging.error(f'An error occurred: {e}')
        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    finally:

        # Closes the connection to the SQL DB once the function completes. This is to avoid a "leaked" connection.
        if conn is not None:
            conn.close()

@app.timer_trigger(schedule="0 0 9 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
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
                    I want to compare last week with this week. Please advise me of the following:
                    1. Any new visitors and how many visits they have
                    2. Any changes in visit counts
                    3. Any other interesting trends that you've noticed.
                    4. Take today's date {thisweek} and tell me an interesting historical thing that happened on the same date.
                    Last Week:
                    {data_lastweek}
                    This week:
                    {data_thisweek}'''

        client = AsyncOpenAI(
         api_key=os.environ['OPENAI_API_KEY'],  # Reference the API key in my function app environment
        )
        response = await client.chat.completions.create(model="gpt-3.5-turbo",messages=[{"role": "user", "content": prompt}])
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
                "subject": f"Visitors analysis of {thisweek}",
                "plainText": f"{promptresponse}",
            }
        }

        poller = client.begin_send(message)
        poller.result()

    except Exception as e:
        # Log any exceptions that occur
        logging.error(f"An error occurred: {e}")

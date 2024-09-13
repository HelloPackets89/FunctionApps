import os
import pyodbc
from azure.storage.blob import BlobClient, BlobServiceClient
import datetime
from openai import AzureOpenAI
import logging
import azure.functions as func
from azure.core.exceptions import ResourceNotFoundError
from azure.communication.email import EmailClient

app = func.FunctionApp()

#The timer trigger decorator is what defines when and how often my function is running.
#The retry decorator defines how often my app will try again if it fails for whatever reason. 
#Both of these decorators have the "power" to make my function app run again 
#FYI Azure CRON jobs are in UTC.. not local time
#If you change the cadence of the cronjob you also need to update the delta for lastweek's checks. A daily cronjob is a delta of -1.
@app.timer_trigger(schedule="0 45 8 * * 5", arg_name="myTimer", run_on_startup=False,use_monitor=False) 
@app.retry(strategy="fixed_delay", max_retry_count="5",delay_interval="00:00:01")
def dbqueryandsave(myTimer: func.TimerRequest, context: func.Context) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')
#1 - DB Connect Test
        # Create a new connection
        conn_str = os.getenv('SQLDB_CONNECTION_STRING')
        conn = pyodbc.connect(conn_str)
        if conn:
            sqlstate_result = f'#1 - Successfully connected to the DB after {context.retry_context.retry_count + 1} attempts'
            logging.warning(sqlstate_result)
        # Create a cursor from the connection. The cursor is what interacts with my database. 
        # The cursor can be used to "move around" the database and fetch individual rows. I'm just printing everything. 
        cur = conn.cursor()

        # Get the connection strings from the environmental settings
        # This connects to my blob storage and my SQL DB
        blob_service_client = BlobServiceClient.from_connection_string(os.getenv('AzureWebJobsStorage'))
#2 - Blob Storage Connection Test
        if blob_service_client:
            blob_service_client_result = '#2 - Connected to Blob storage successfully'
            logging.warning(blob_service_client_result)
        else:
            blob_service_client_result = '#2 - Connection to Blob storage failed'
            logging.error(blob_service_client_result)

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
#3 - Query DB Test
        if all_rows_str:
            all_rows_str_result = '#3 - Queried DB successfully'
            logging.warning(all_rows_str_result)
        else:
            all_rows_str_result = '#3 - Query DB unsuccessfully'
            logging.error(all_rows_str_result)
        # Upload all the results to the storage account using the predefined filename. 
        # If this file already exists, the attempt to upload will fail. This is intentional. 
        blob_client.upload_blob(all_rows_str)
#4 - Confirm upload was successful
        blob_data = blob_client.download_blob()
        blob_contents = blob_data.readall()
        if blob_contents:
            blob_contents_results = (f'#4 - Uploaded data to {filename} successfully')
            logging.warning(blob_contents_results)
        else:
            blob_contents_results = (f'#4 - Failed to upload data to {filename}')
            logging.error(blob_contents_results)
       
    # Error logging - this section provides more verbose errors if the function app fails for whatever reason.\
    # \n refers to printing a new line
    # this error logging was ripped from microsoft learn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0] if len(ex.args) > 0 else None
        sqlstate_result =(f'Database error occurred:\nSQLState: {sqlstate}\nError: {ex}')
        logging.error(sqlstate_result)
        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.error(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    except Exception as e:
        logging.error(f'An error occurred: {e}')
        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    finally:
#5 - Confirm DB Connection closes
        # Closes the connection to the SQL DB once the function completes. This is to avoid a "leaked" connection.
        if conn is not None:
            conn.close()
            dbclose_result = ('#5 - Connection to DB was closed successfully.')
            logging.warning(dbclose_result)
        else:
            dbclose_result = ('#5 - Connection to DB was not closed successfully')
            logging.error(dbclose_result)


#Upload results of Smoketests 1 - 5
        tests1to5 = f'''
                    {sqlstate_result}
                    {blob_service_client_result}
                    {all_rows_str_result}
                    {blob_contents_results}
                    {dbclose_result}'''
        smoketests_filename = f"smoketests_{today}.txt"
        smoketest_blob_client = blob_service_client.get_blob_client("smoketests", smoketests_filename)
        smoketest_blob_client.upload_blob(tests1to5)

#FYI Azure CRON jobs are in UTC.. not local time
@app.timer_trigger(schedule="0 0 9 * * 5", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
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
        lastweek = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y%m%d")
        lastweektxt = f"visitors{lastweek}.txt"
        thisweek = datetime.date.today().strftime("%Y%m%d")
        thisweektxt = f"visitors{thisweek}.txt"
        # Setup the blob connections for this week and last week
        blob_lastweek = BlobClient.from_connection_string(blobkey, "results", lastweektxt)
        blob_thisweek = BlobClient.from_connection_string(blobkey, "results", thisweektxt)
        # Convert the txt inside the files to something that's useable
 #6 - Check access to last week's results
        try:
            data_lastweek = blob_lastweek.download_blob().readall().decode('utf-8')
            if data_lastweek:
                blob_lastweek_result = (f"#6 - Access to {lastweektxt} was successful.")
                logging.warning(blob_lastweek_result)
        except ResourceNotFoundError:
            blob_lastweek_result = (f"#6 - Could not find blob {lastweektxt} in container 'results'")
            logging.error(blob_lastweek_result)
            return
#7 - Check access to this week's results
        try:
            data_thisweek = blob_thisweek.download_blob().readall().decode('utf-8')
            if data_thisweek:
                data_thisweek_result = (f"#7 - Access to {thisweektxt} was successful.")
                logging.warning(data_thisweek_result)            
        except ResourceNotFoundError:
            blob_thisweek_result = (f"#7 - Could not find blob {thisweektxt} in container 'results'")
            logging.error(blob_thisweek_result)
            return
        #Define the prompt I want to be using that includes a reference to the data contained in the text files.
        prompt = f'''I have two sets of results that display the Public IP address of my visitors and how many times they've visited. 
                    I want to compare last week's visit tally with today. Please advise me of the following:
                    1. Any new visitors or changes in visit count
                    2. Any other interesting trends that you've noticed.
                    3. Take today's date {thisweek} and tell me an interesting historical thing that happened on the same date.
                    Last week:
                    {data_lastweek}
                    Today:
                    {data_thisweek}'''

        client = AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = "2024-02-01",
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        logging.warning(client)

        
#8 - Confirm API connected successfully.
        try:
            response_test = client.chat.completions.create(model="BrandonAI", messages=[{"role": "user", "content": 'Hello Mr.AI are you there?'}])
            response_test_response = (response_test.choices[0].message.content)
            if response_test_response:
                response_result = ("#8 - Connection to Azure OpenAI was successful")
                logging.warning(response_result)
            else:
                response_result = ("#8 - Connection to Azure OpenAI failed.")
                logging.error(response_result)
        except Exception as e:
                logging.error(f"An error occurred: {e}")

        try:
            response = client.chat.completions.create(
                model="BrandonAI", # model = "deployment_name".
                messages=[{"role": "user", "content": prompt}])
            # Log the content of the first message in the completion choices
            promptresponse = (response.choices[0].message.content)
            logging.warning(promptresponse)
#9 - Confirm a response is received for the prompt
            if promptresponse:
                promptresponse_result = ("#9 - Prompt was successful, received a response.")
                logging.warning(promptresponse_result)     
            else:
                promptresponse_result = ("#9 - Prompt was not successful, did not receive response.")
                logging.error(promptresponse_result)                           
        except Exception as e:
        # Log any exceptions that occur
            logging.error(f"An error occurred: {e}")         
        #Email the results to me
        emailkey = os.environ.get('EMAIL_KEY')
        client = EmailClient.from_connection_string(emailkey)
#10 - Include all results in the email 
        tests1to5_resultstxt = f"smoketests_{thisweek}.txt"
        blob_tests1to5_results = BlobClient.from_connection_string(blobkey, "smoketests", tests1to5_resultstxt)
        data_tests1to5_results = blob_tests1to5_results.download_blob().readall().decode('utf-8')

        all_results = f'''
                    {data_tests1to5_results}
                    {blob_lastweek_result}
                    {data_thisweek_result}
                    {response_result}
                    {promptresponse_result}
                    #10 - Email sent successfully
                    '''
        message = {
            "senderAddress": "visitormonitor@brandedkai.net",
            "recipients":  {
                "to": [{"address": "brandon@allmark.me" }],
            },
            "content": {
                "subject": f"Visitors analysis of {thisweek}",
                "plainText": f"{promptresponse} {all_results}",
            }
        }

        poller = client.begin_send(message)
        poller.result() 
#10 - Confirm email sent successfully
        poller_result = poller.result() 
        if poller_result:
            email_result = '#10 - Email sent successfully'
            logging.warning(email_result)
        else:
            email_result = '#10 - Email failed to send'
            logging.error(email_result)

    except Exception as e:
        # Log any exceptions that occur
        logging.error(f"An error occurred: {e}")

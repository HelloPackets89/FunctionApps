import logging
import azure.functions as func
import os
import pyodbc
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import datetime


app = func.FunctionApp()

#The timer trigger decorator is what defines when and how often my function is running.
#The retry decorator defines how often my app will try again if it fails for whatever reason. 
#Both of these decorators have the "power" to make my function app run again 
@app.timer_trigger(schedule="0 30 16 * * 5", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
@app.retry(strategy="fixed_delay", max_retry_count="3",
           delay_interval="00:00:01")
def timer_trigger1(myTimer: func.TimerRequest, context: func.Context) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        # Get the connection string from the environmental settings
        #This connects to my blob storage and my SQL DB
        conn_str = os.getenv('SQLDB_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(os.getenv('AzureWebJobsStorage'))
        logging.info('Attempting connection')
        # Create a new connection
        conn = pyodbc.connect(conn_str)

        # Create a cursor from the connection
        cur = conn.cursor()
        logging.info('Attempting query..')
        # Execute a query
        cur.execute("SELECT TOP (1000) * FROM ResumeVisitors")

        # Create a blob client using the local file name as the name for the blob
        #putting "f" infront of strings means it parses the variables inside the string, instead of just putting the name of the variable. 
        today = datetime.date.today().strftime("%Y%m%d")
        filename = f"visitors{today}.txt"
        blob_client = blob_service_client.get_blob_client("results", filename)

        #Fetch all the results of the query and add it to my file
        rows = cur.fetchall()
        all_rows = []
        #For each row found in the query results, combine them into one string. 
        for row in rows:
            all_rows.append(str(row))

        #all_rows_str = '\\n'.join(all_rows)
        #logging.info(all_rows_str)
        logging.info(all_rows)
        # Upload the row to the blob
        blob_client.upload_blob(all_rows, blob_type="AppendBlob")

    #Error logging - this section provides more verbose errors if the function app fails for whatever reason.
    except pyodbc.Error as ex:
        sqlstate = ex.args[0] if len(ex.args) > 0 else None
        logging.error(f'Database error occurred:\\nSQLState: {sqlstate}\\nError: {ex}')
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

    logging.info('Python timer trigger function executed.')

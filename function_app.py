import logging
import azure.functions as func
import os
import pyodbc
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

app = func.FunctionApp()

@app.timer_trigger(schedule="0 30 16 * * 5", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
@app.retry(strategy="fixed_delay", max_retry_count="3",
           delay_interval="00:00:01")
def timer_trigger1(myTimer: func.TimerRequest, context: func.Context) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        # Get the connection string from the environmental settings. This is the connection string of the Azure SQL DB you want to connect to. 
        conn_str = os.getenv('SQLDB_CONNECTION_STRING')
        logging.info('Attempting connection')
        # Create a new connection
        conn = pyodbc.connect(conn_str)

        # Create a cursor from the connection
        cur = conn.cursor()
        logging.info('Attempting query..')
        # Execute a query
        cur.execute("SELECT TOP (1000) * FROM ResumeVisitors")

        # Fetch all rows from the last executed statement
        rows = cur.fetchall()

        # Create a BlobServiceClient object which will be used to create a container client
        blob_service_client = BlobServiceClient.from_connection_string(os.getenv('AzureWebJobsStorage'))

        # Create a blob client using the local file name as the name for the blob
        blob_client = blob_service_client.get_blob_client("results", "visitors.txt")

        for row in rows:
            logging.info(row)
            # Upload the row to the blob
            blob_client.upload_blob(str(row), blob_type="AppendBlob")

    #Error logging - this section provides more verbose errors if the function app fails for whatever reason.
    #It also makes the attempt to connect again. Embrace the jank.
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

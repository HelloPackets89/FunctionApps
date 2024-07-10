import logging
import azure.functions as func
import os
import pyodbc
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
#if any of these are showing as "Could not be resolved" then you need to pip install them and if that doesn't work you should see which .venv you have active


app = func.FunctionApp()

@app.timer_trigger(schedule="0 30 16 * *5", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
def timer_trigger1(myTimer: func.TimerRequest) -> None:
    max_attempts = 5
    conn = None
    
    for attempt in range(max_attempts):
        try:
            if myTimer.past_due:
                logging.info('The timer is past due!')
            
            # Get the connection string from the environmental settings
            conn_str = os.getenv('SQLDB_CONNECTION_STRING')
            logging.info(f'Attempting connection (Attempt {attempt + 1} of {max_attempts})')
            
            # Create a new connection
            conn = pyodbc.connect(conn_str)
            
            # Create a cursor from the connection
            with conn.cursor() as cur:
                logging.info('Attempting query...')
                # Execute a query
                cur.execute("SELECT TOP (1000) * FROM ResumeVisitors")
                # Fetch all rows from the last executed statement
                rows = cur.fetchall()
                for row in rows:
                    logging.info(row)
            
            logging.info('Query executed successfully')
            return  # Exit the function after successful execution
        
        except pyodbc.Error as ex:
            sqlstate = ex.args[0] if len(ex.args) > 0 else None
            logging.error(f'Database error occurred:\nSQLState: {sqlstate}\nError: {ex}')
        except Exception as e:
            logging.error(f'An error occurred: {e}')
        
            if attempt < max_attempts - 1:
                logging.info(f'Retrying... (Attempt {attempt + 2} of {max_attempts})')
            else:
                logging.error(f'Failed after {max_attempts} attempts.')

        finally:

            # Closes the connection to the SQL DB once the function completes. This is to avoid a "leaked" connection.
            if conn is not None:
                conn.close()

    logging.info('Python timer trigger function executed.')
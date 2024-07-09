import logging
import azure.functions as func
import os
import pyodbc

app = func.FunctionApp()

@app.timer_trigger(schedule="0 30 16 * * 5", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger1(myTimer: func.TimerRequest) -> None:
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if myTimer.past_due:
                logging.info('The timer is past due!')

            # Get the connection string from the environmental settings. This is the connection string of the Azure SQL DB you want to connect to. 
            conn_str = os.getenv('SQLDB_CONNECTION_STRING')

            # Create a new connection
            conn = pyodbc.connect(conn_str)

            # Create a cursor from the connection
            cur = conn.cursor()

            # Execute a query
            cur.execute("SELECT TOP (1000) * FROM ResumeVisitors")

            # Fetch all rows from the last executed statement
            rows = cur.fetchall()

            for row in rows:
                logging.info(row)
            break # This causes the loop to break as hitting this point signifies a successful run. 

    #Error logging - this section provides more verbose errors if the function app fails for whatever reason
        except pyodbc.Error as ex:
            sqlstate = ex.args[0] if len(ex.args) > 0 else None
            logging.error(f'Database error occurred:\nSQLState: {sqlstate}\nError: {ex}')
            if attempt < max_attempts - 1:  # This is because ranges start at 0. So attempt 4, is actually attempt 5. 
                logging.info(f'Retrying... (Attempt {attempt + 1} of {max_attempts})')
            else:
                logging.error(f'Failed after {max_attempts} attempts.')
        except Exception as e:
            logging.error(f'An error occurred: {e}')
        finally:

            # Closes the connection to the SQL DB once the function completes. This is to avoid a "leaked" connection.
            conn.close()

    logging.info('Python timer trigger function executed.')
import logging
import azure.functions as func
import os
import pyodbc

app = func.FunctionApp()

@app.timer_trigger(schedule="0 30 16 * * 5", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger1(myTimer: func.TimerRequest) -> None:
    try:
        if myTimer.past_due:
            logging.info('The timer is past due!')

        # Get the connection string from the application settings
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

    except pyodbc.Error as ex:
        sqlstate = ex.args[0] if len(ex.args) > 0 else None
        logging.error(f'Database error occurred:\nSQLState: {sqlstate}\nError: {ex}')
    except Exception as e:
        logging.error(f'An error occurred: {e}')
    finally:

        # Don't forget to close the connection
        conn.close()

    logging.info('Python timer trigger function executed.')
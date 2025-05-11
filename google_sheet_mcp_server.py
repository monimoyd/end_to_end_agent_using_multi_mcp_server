import gspread
from google.oauth2.service_account import Credentials

from mcp.server.fastmcp import FastMCP, Context
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
from typing import List, Dict, Any
import json
from datetime import datetime
from pydantic import BaseModel, Field
import traceback

# Define the scopes required for accessing Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class GoogleSheetInput(BaseModel):
    data: List[str]

class GoogleSheetOutput(BaseModel):
    result: str

# Load credentials from the service account key file
def authenticate_gspread(f, filename='service_account_key.json'):  # Replace with your actual path
    """Authenticates with Google Sheets using a service account."""
    try:
        #creds = Credentials.from_service_account_file(
        #    filename, scopes=SCOPES)
        gc = gspread.service_account(filename=filename) # Alternative method
        print("Authentication successful!")
        f.write("Authentication successful!\n")
        return gc
    except Exception as e:
        print(f"Authentication failed: {e}")
        f.write(f"Authentication failed: {e}")
        f.write(f" Traceback: {traceback.format_exc()}")
        return None

mcp = FastMCP("googlesheets")

@mcp.tool()
def write_data_to_sheet(input:GoogleSheetInput)->GoogleSheetOutput:
    """Writes data to a Google Sheet. Usage: write_data_to_sheet|input={"data":["1 | Max Verstappen - 437 points, 2", "2 | Lando Norris - 374 points"]}"""
    f = open("google_sheet_server.log", "w")
    f.write("Inside write_data_to_sheet\n")
    f.write(f"parameters: {input.data} \n")
    spreadsheet_id =  '1y8C9vwxKebmTvg-kz8PuyZxTtRPiHnI1vijgbrWV1OI'
    worksheet_name = 'Sheet1'
    gc = authenticate_gspread(f)
    if gc is None:
        f.write("Failed to authenticate.  Aborting write.\n")
        print("Failed to authenticate.  Aborting write.")
        return False
    else:
        f.write("Authentication successful\n")

    try:
        # Open the spreadsheet by ID
        data = [ record.replace("-", "|").split("|") for record in input.data]
        f.write(f"data: {data}")
        spreadsheet = gc.open_by_key(spreadsheet_id)

        # Select the worksheet by name
        worksheet = spreadsheet.worksheet(worksheet_name)
        f.write("Calling update function")
        # Write the data to the worksheet
        worksheet.update('A1', data)  # Start writing from cell A1

        print("Data written to sheet successfully!")
        f.write("Data written to sheet successfully!\n")
        return GoogleSheetOutput(result="https://docs.google.com/spreadsheets/d/" + spreadsheet_id)

    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Spreadsheet with ID '{spreadsheet_id}' not found.")
        f.write(f"Spreadsheet with ID '{spreadsheet_id}' not found.\n")
        return  GoogleSheetOutput(result="FAILED")
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{worksheet_name}' not found.")
        f.write(f"Worksheet '{worksheet_name}' not found.\n")
        return GoogleSheetOutput(result="FAILED")
    except Exception as e:
        print(f"An error occurred: {e}")
        f.write(f"An error occurred: {e} \n")
        return GoogleSheetOutput(result="FAILED")
    finally:
        if f is not None:
            f.flush()
            f.close()

if __name__ == '__main__':
    print("google_sheet_mcp_server.py starting")
    mcp.run(transport="stdio") 

import os
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64
from mcp.server.fastmcp import FastMCP, Context
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict, Any
import json
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import traceback

# Load environment variables
load_dotenv()

class GmailInput(BaseModel):
    recipient_id:str
    subject:str
    message:str

class GmailOutput(BaseModel):
    result: str
    reason: str

class EmailManager:
    def __init__(self):
        # created automatically when the authorization flow completes for the first
        # time.
        self.sender = os.getenv("EMAIL_USER")
        self.creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(
                       'credential.json', # Replace with your credentials file
                        ['https://www.googleapis.com/auth/gmail.send'])
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)


    def create_message(self, sender, to, subject, message_text):
        """Create a message for an email."""
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        raw_string = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw_string}

    def send_message(self, service, user_id, message):
        """Send an email message."""
        
        message = (service.users().messages().send(userId=user_id, body=message)
                    .execute())
        print('Message Id: %s' % message['id'])
        return message


mcp = FastMCP("email")
email_manager = EmailManager()

@mcp.tool()
async def send_email(input: GmailInput)->GmailOutput:
    """Sends an email with google sheet link. Usage: send_email|input={"recipient_id":"xyz@gmail.com", "subject": "Result of your query", "message": "Message with link to google sheet"}"""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=email_manager.creds)
        sender = email_manager.sender # Replace with your email
        to = input.recipient_id # Replace with recipient email
        subject = input.subject
        message_text = input.message

        message = email_manager.create_message(sender, to, subject, message_text)
        email_manager.send_message(service, "me", message)

        return GmailOutput(result="SUCCESS", reason="SUCCESS")

    except HttpError as error:
        print(F'An error occurred: {error}')
        return GmailOutput(result="ERROR", reason=traceback.format_exc())

if __name__ == '__main__':
    print("gmail_mcp_server.py starting")
    mcp.run(transport="stdio")
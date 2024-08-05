from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os.path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
#import pdfkit

#pdfkit.from_url('https://google.com', 'out.pdf')


app = FastAPI()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
# SCOPES = ["https://www.googleapis.com/auth/drive.file"]



@app.get("/download/")
async def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)

        # Call the Drive v3 API
        results = (
            service.files()
            .list(pageSize=10, fields="nextPageToken, files(id, name)")
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print("No files found.")
            return
        print("Files:")
        for item in items:
            print(f"{item['name']} ({item['id']})")
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")


# Path to your service account key file
SERVICE_ACCOUNT_FILE = 'token.json'
# # Scopes required to access Google Drive API
# SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# # Authenticate using the service account file
credentials = Credentials.from_authorized_user_file("token.json", SCOPES)

# # Build the Drive API client
drive_service = build('drive', 'v3', credentials=credentials)


@app.get("/download/{file_id}")
async def download_file(file_id: str):
    try:
        # Request the file from Google Drive
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f'Download {int(status.progress() * 100)}%.')

        # Save the downloaded file to your local filesystem
        fh.seek(0)
        local_file_path = f"/tmp/{file_id}.download"
        with open(local_file_path, 'wb') as f:
            f.write(fh.read())

        return FileResponse(local_file_path, media_type='application/octet-stream', filename=f"{file_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import os
import time
from dotenv import load_dotenv
from google import genai
from pathlib import Path

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

def get_transcript_from_video(file_path: str) -> str:
    """
    Uploads a video or audio file to Google Gemini and returns the transcript.
    Works for mp4, mp3, wav, etc.
    """
    print(f"Uploading {file_path} ")
    
    # 1. Initialize the Google GenAI client for file handling
    client = genai.Client(
        api_key=api_key
    )
    
    # 2. Upload the file
    try:
        uploaded_file = client.files.upload(file=file_path)
        print(f"File uploaded. File name: {uploaded_file.name}")
    except Exception as e:
        return f"Failed to upload file: {e}"

    # 3. Wait for the file to be processed (video processing takes time)
    # The file state must be "ACTIVE" before you can prompt against it.
    print("Waiting for process the file...")
    while True:
        file_info = client.files.get(name=uploaded_file.name)
        if file_info.state == "ACTIVE":
            print("File is ready!")
            break
        elif file_info.state == "FAILED":
            return "File processing failed on Ai end."
        
        print("Still processing, waiting 10 seconds...")
        time.sleep(10)

    # 4. Ask Gemini to transcribe the processed file. The GenAI SDK accepts
    # the uploaded file object directly; LangChain does not support a "file"
    # message part in this format.
    print("Generating transcript...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            file_info,
            "Please provide a highly accurate, word-for-word transcript "
            "of this audio/video. Do not summarize. Just provide the transcript.",
        ],
    )
    
    return response.text

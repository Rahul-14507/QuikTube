import os
import re
import requests
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from google.oauth2 import credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# --- T5-Small Specific Imports ---
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
# --- End T5-Small Specific Imports ---

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Global variables for Model Configuration ---
# ### T5-Small Specific Changes ###
T5_MODEL = None
T5_TOKENIZER = None
T5_MODEL_NAME = "t5-small" # The name of the T5 model
MODEL_LOAD_ERROR = ""
# --- End T5-Small Specific Changes ---

# --- Model Loading (T5-Small) ---
# ### T5-Small Specific Changes ###
try:
    print(f"Loading T5-Small model: {T5_MODEL_NAME}...")
    T5_TOKENIZER = AutoTokenizer.from_pretrained(T5_MODEL_NAME)
    T5_MODEL = AutoModelForSeq2SeqLM.from_pretrained(T5_MODEL_NAME)
    # Move model to GPU if available for faster inference
    if torch.cuda.is_available():
        T5_MODEL.to("cuda")
        print("T5-Small model loaded onto GPU.")
    else:
        print("T5-Small model loaded onto CPU (GPU not available).")
    
    print("T5-Small model configured successfully.")
except Exception as e:
    MODEL_LOAD_ERROR = f"Error loading T5-Small model: {e}. Make sure you have 'transformers' and 'torch' installed."
    print(MODEL_LOAD_ERROR)
# --- End T5-Small Specific Changes ---


# --- OAuth 2.0 Setup ---
# CORRECTED SCOPES: Only youtube.readonly and youtube.captions.readonly
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly', 'https://www.googleapis.com/auth/youtube.captions.readonly']
CREDENTIALS_PATH = 'credentials.json' # Path to your downloaded credentials.json file

def get_youtube_service():
    """
    Builds and returns an authenticated YouTube Data API service object.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = credentials.Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                 print(f"Error refreshing credentials: {e}")
                 return None # Return None on refresh failure
        else:
            # Use the correctly imported InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)  # This will open a browser window for the user to authenticate
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    if not creds:
        print("Failed to retrieve or refresh credentials.")
        return None # Return None if credentials are not available

    return googleapiclient.discovery.build('youtube', 'v3', credentials=creds)


# Helper function to extract video ID from YouTube URL
def get_video_id_from_url(url):
    """
    Extracts the video ID from various YouTube URL formats using regex.
    """
    # Use a raw string (r'...') to avoid SyntaxWarnings about escape sequences
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=|)'
        r'([A-Za-z0-9_-]{11})' # This is the 11-character video ID
        r'([^#&?]*).*' # Any remaining characters before #, &, or ?
    )

    match = re.match(youtube_regex, url)
    if match:
        return match.group(6) # The video ID is typically in the 6th group
    return None

def get_transcript_from_youtube_api(youtube_url):
    """Fetches the transcript from YouTube using the Data API with OAuth 2.0."""
    video_id = get_video_id_from_url(youtube_url)
    if not video_id:
        return None, None, "Invalid YouTube URL format for transcript extraction."

    try:
        youtube = get_youtube_service()
        if not youtube:
            return None, None, "Failed to initialize YouTube service with OAuth 2.0."

        # Get video details to confirm title and if captions exist
        video_request = youtube.videos().list(
            part="snippet,contentDetails",
            id=video_id
        )
        video_response = video_request.execute()
        video_title = video_response.get("items", [{}])[0].get("snippet", {}).get("title", "Unknown Video")

        # Check if captions are even available for the video
        if not video_response.get("items", [{}])[0].get("contentDetails", {}).get("caption", "false") == "true":
            return video_title, None, "Video does not have captions."

        # List available captions for the video
        caption_request = youtube.captions().list(
            part="snippet", videoId=video_id
        )
        caption_response = caption_request.execute()

        caption_id = None
        for item in caption_response.get("items", []):
            if item["snippet"]["language"] == "en":  # Prioritize English
                caption_id = item["id"]
                break

        if not caption_id:
            # Fallback to auto-generated if no official English found
            for item in caption_response.get("items", []):
                if item["snippet"]["language"] == "en" and item["snippet"].get("trackKind") == "ASR":  # ASR means Automatic Speech Recognition
                    caption_id = item["id"]
                    print(f"Found auto-generated English captions for {video_title}.")
                    break

        if not caption_id:
            return video_title, None, "No suitable English captions found for this video (neither official nor auto-generated)."

        # Download the caption track
        caption_download_request = youtube.captions().download(
            id=caption_id, tfmt="vtt"
        )
        caption_download_response = caption_download_request.execute()

        # Basic VTT parsing (assuming it's VTT format)
        lines = caption_download_response.decode('utf-8').split('\n')
        clean_transcript_lines = []
        for line in lines:
            if '-->' not in line and not line.strip().isdigit() and line.strip() != '' and \
                    not line.startswith('WEBVTT') and not line.startswith('Kind:') and not line.startswith('Language:'):
                clean_transcript_lines.append(line.strip())

        transcript_text = " ".join(clean_transcript_lines)
        return video_title, transcript_text, None

    except HttpError as e:
        return None, None, f"YouTube Data API HTTP error: {e.resp.status} - {e.content.decode('utf-8')}"
    except Exception as e:
        return None, None, f"An unexpected error occurred during YouTube Data API call: {e}"

# --- Routes ---

@app.route('/')
def index():
    # ### T5-Small Specific Changes ###
    if T5_MODEL is None or T5_TOKENIZER is None:
        return f"YouTube Summarizer Backend is running, but T5-Small model failed to load: {MODEL_LOAD_ERROR}", 500
    # --- End T5-Small Specific Changes ---

    return f"YouTube Summarizer Backend is running using {T5_MODEL_NAME} for summarization!"


@app.route('/summarize', methods=['POST'])
def summarize_video():
    # ### T5-Small Specific Changes ###
    if T5_MODEL is None or T5_TOKENIZER is None:
        return jsonify({
            "error": f"T5-Small model not loaded: {MODEL_LOAD_ERROR}",
            "video_title": "Configuration Error"
        }), 500
    # --- End T5-Small Specific Changes ---

    data = request.get_json()
    youtube_url = data.get('url')

    if not youtube_url:
        return jsonify({"error": "No YouTube URL provided", "video_title": "Error"}), 400

    print(f"Received URL for summarization: {youtube_url}")

    video_title = "Unknown Video"
    transcript_text = ""
    transcript_error = None # To store error message from transcript fetching

    try:
        # --- YouTube Data API for Title and Transcript Extraction ---
        video_title, transcript_text, transcript_error = get_transcript_from_youtube_api(youtube_url)

        if transcript_error:
            print(f"Transcript extraction warning/error: {transcript_error}")
            if not transcript_text: # If no transcript was returned at all
                print("No transcript extracted. Summarization will fail without transcript for T5-Small.")
                # T5-Small generally doesn't work well on just a URL.
                return jsonify({
                    "error": f"Failed to extract transcript: {transcript_error}. T5-Small requires a transcript for summarization.",
                    "video_title": video_title
                }), 500 # Return an error because T5-Small won't do much with just a URL
        elif transcript_text:
            print(f"Extracted transcript (first 200 chars): {transcript_text[:200]}...")
            print("Summarizing from extracted transcript using T5-Small.")

        # Ensure video_title is set even if transcript failed
        if not video_title:
            video_title = "Unknown Video"

        # --- T5-Small Summarization ---
        # ### T5-Small Specific Changes ###
        # T5-Small expects a specific input format for summarization
        input_text = "summarize: " + transcript_text

        # Tokenize the input text
        # max_length is important to avoid exceeding model's context window, typically 512 for T5-Small
        # truncation=True ensures long texts are cut, but you might want to split them for better results
        inputs = T5_TOKENIZER(input_text, return_tensors="pt", max_length=1024, truncation=True)

        # Move inputs to GPU if model is on GPU
        if torch.cuda.is_available():
            inputs = {key: value.to("cuda") for key, value in inputs.items()}

        # Generate summary
        summary_ids = T5_MODEL.generate(
            inputs["input_ids"],
            max_length=150, # Max length of the generated summary
            min_length=40,  # Min length of the generated summary
            length_penalty=2.0, # Encourages longer summaries
            num_beams=4,    # For beam search (better quality, slower)
            early_stopping=True
        )

        # Decode the generated summary
        summary = T5_TOKENIZER.decode(summary_ids[0], skip_special_tokens=True)
        # --- End T5-Small Specific Changes ---

        print(f"Generated summary: {summary}")
        return jsonify({
            "summary": summary,
            "video_title": video_title,
            "youtube_url": youtube_url
        }), 200

    except Exception as e:
        error_message = f"An unexpected error occurred during summarization: {e}"
        print(error_message)
        return jsonify({"error": error_message, "video_title": video_title}), 500


if __name__ == '__main__':
    # Ensure this part is the last thing, as it starts the Flask server
    app.run(debug=True, host='0.0.0.0', port=5000)
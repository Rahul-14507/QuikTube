# QuickTube

## Description

QuickTube is a Flutter mobile application designed to provide instant summaries of YouTube videos in actionable bullet points. It addresses the need for efficient learning and eliminates the time-waste associated with watching lengthy videos. QuickTube is ideal for individuals seeking self-growth who have limited time.

## Features

*   **YouTube Transcript Fetching:** Automatically retrieves transcripts from YouTube videos.
*   **AI-Powered Summarization:** Utilizes T5-small, GPT API, or Gemini API to generate concise summaries.
*   **Actionable Bullet Points:** Presents summaries as easy-to-digest bullet points for quick understanding.
*   **User-Friendly Mobile Interface:** Offers a seamless and intuitive experience on mobile devices.

## Technologies Used

*   **Frontend:** Flutter
*   **Backend:** Flask (Python)
*   **Summarization Models/APIs:** T5-small, GPT API, Gemini API
*   **Data Storage:** Supabase
*   **YouTube Integration:** YouTube Data API

## Setup Instructions

Follow these steps to set up the QuickTube development environment:

### 1. Prerequisites

*   Flutter SDK: [https://flutter.dev/docs/get-started/install](https://flutter.dev/docs/get-started/install)
*   Python 3.x: [https://www.python.org/downloads/](https://www.python.org/downloads/)
*   Android Studio or VS Code with Flutter extension
*   Supabase account and project: [https://supabase.com/](https://supabase.com/)

### 2. Clone the Repository

> bash
> cd backend  # Navigate to the backend directory
> python3 -m venv venv
> source venv/bin/activate # On Windows use `venv\Scripts\activate`
> pip install -r requirements.txt
> > Create a `.env` file in the `backend` directory and add your API keys and Supabase credentials:

> bash
> python app.py
> > In `main.dart` or your relevant service file, initialize Supabase with your project URL and API key.

> 1.  **Download and Open:** Download the QuickTube repository and open it in Android Studio or VS Code.
2.  **Run Backend:** Ensure the Flask backend server is running by navigating to the `backend` directory, activating the virtual environment, and executing `python app.py`.
3.  **Connect Device/Emulator:** Connect your physical Android/iOS device or start an emulator.
4.  **Run Flutter App:** In the `frontend` directory, run the Flutter application using the `flutter run` command.
5.  **Enter YouTube URL:** Enter the URL of the YouTube video you want to summarize into the app.
6.  **View Summary:** The app will display the summarized bullet points of the video.

## Contribution Guidelines

We welcome contributions to QuickTube! To contribute:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and ensure they are well-tested.
4.  Submit a pull request with a clear description of your changes.

## License Information
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

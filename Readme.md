# Tale Weaver - Interactive Story Generator

A dynamic, AI-powered interactive fiction application where users shape their own narrative adventure through choices and input. Built with Streamlit and Google's Gemini-2.0-flash API.

## Features

- Dynamic story generation across multiple genres
- Branching narrative paths based on user choices
- Personalized storytelling with custom character names
- Story saving functionality
- Responsive and immersive UI

## Local Setup

1. Clone this repository
2. Create a `.env` file in the root directory with your Gemini API key:
   ```
   GEMINI_API_KEY=your-api-key-here
   ```
3. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
4. Run the app:
   ```
   streamlit run app.py
   ```

## Deployment to Heroku

1. Create a new Heroku app:
   ```
   heroku create your-app-name
   ```

2. Set the Gemini API key as a config variable:
   ```
   heroku config:set GEMINI_API_KEY=your-api-key-here
   ```

3. Deploy the app:
   ```
   git push heroku main
   ```

4. Open the app:
   ```
   heroku open
   ```

## Project Structure

```
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── Procfile            # Heroku deployment configuration
├── runtime.txt         # Python version specification
├── .env                # Local environment variables (not in git)
├── README.md           # Project documentation
└── saved_stories/      # Directory for saved stories (created at runtime)
```

## How It Works

1. **Welcome Screen**: Introduction to the app and instructions
2. **Setup**: Choose genre, character name, and starting scenario
3. **Story**: Interactive storytelling with branching paths based on user choices
4. **Save**: Option to save stories for later reference

## Technologies Used

- Streamlit for the web interface
- Google's Gemini-2.0-flash API for AI-powered story generation
- Python for backend logic

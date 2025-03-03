import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import uuid
import time
from datetime import datetime
import re
import base64
from gtts import gTTS

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Set page configuration
st.set_page_config(
    page_title="Tale Weaver - Interactive Story Generator",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Ensure required folders exist
if not os.path.exists("saved_stories"):
    os.makedirs("saved_stories")

# Audio folder for TTS files
if not os.path.exists("audio_files"):
    os.makedirs("audio_files")

# Initialize or load session state
if "story_state" not in st.session_state:
    st.session_state.story_state = {
        "story_id": str(uuid.uuid4()),
        "current_text": "",
        "choices_made": [],
        "path_taken": [],
        "genre": "",
        "character_name": "",
        "stage": "welcome",  # welcome, setup, story, ending
        "story_turns": 0,    # Track story progression
        "word_count": 0      # Track total word count
    }

# TTS function - generates audio and returns HTML for audio player
def text_to_speech(text, filename=None):
    if not text:
        return None
    
    # Clean text for TTS (remove HTML tags and special markers)
    clean_text = re.sub(r'<[^>]*>', '', text)
    
    # Generate a unique filename if not provided
    if filename is None:
        filename = f"audio_{uuid.uuid4()}.mp3"
    
    file_path = os.path.join("audio_files", filename)
    
    # Generate the audio file
    tts = gTTS(text=clean_text, lang='en', slow=False)
    tts.save(file_path)
    
    # Return the audio file path
    return file_path

# Function to create an audio player HTML
def get_audio_player_html(audio_path):
    audio_file = open(audio_path, 'rb')
    audio_bytes = audio_file.read()
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_file.close()
    
    # Delete the file after reading to save space
    os.remove(audio_path)
    
    html = f'''
    <audio autoplay controls style="width: 100%;">
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    '''
    return html

# Improved styling with better contrast and readability
def load_css():
    st.markdown("""
    <style>
    /* Background with better readability */
    .stApp {
        background-color: #f0f2f6;
        color: #1e1e1e;
    }

    /* Story text container with improved contrast */
    .story-text {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        line-height: 1.8;
        color: #1e1e1e;
        font-size: 1.1rem;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Dialog text styling */
    .dialog {
        color: #0d47a1;
        font-style: italic;
    }

    /* Description text styling */
    .description {
        color: #1e1e1e;
    }

    /* Button styling with better visibility */
    .stButton > button {
        background-color: #4CAF50 !important;
        color: #FFFFFF !important;
        padding: 12px 24px !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 8px !important;
        margin: 5px 0 !important;
        text-align: left !important;
        width: 100% !important;
        white-space: normal !important;
        height: auto !important;
        line-height: 1.5 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }

    /* Add disabled state styling */
.stButton > button:disabled {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
    transform: none !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
}

    /* Button hover effect */
    .stButton > button:hover {
        background-color: #388E3C !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
        transform: translateY(-2px) !important;
    }

    /* Secondary button styling */
    .secondary-button {
        background-color: #2196F3 !important;
        color: #ffffff !important;
        padding: 10px 20px !important;
        font-size: 16px !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }

    .secondary-button:hover {
        background-color: #1976D2 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
    }

    /* Genre badges */
    .genre-badge {
        display: inline-block;
        background-color: #673ab7;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.85rem;
        margin: 5px 5px 5px 0;
    }

    /* Headers with improved visibility */
    .welcome-header {
        font-size: 4rem;
        text-align: center;
        margin-bottom: 30px;
        color: #2E7D32;
        font-family: 'Georgia', serif;
    }

    .section-header {
        font-size: 2rem;
        margin-top: 20px;
        margin-bottom: 15px;
        color: #2E7D32;
        font-family: 'Georgia', serif;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 10px;
    }

    /* Progress indicators */
    .progress-indicator {
        background-color: #e8f5e9;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
        font-size: 0.9rem;
        color: #1e1e1e;
        border-left: 3px solid #4CAF50;
    }

    /* Choice marker */
    .choice-marker {
        color: #2E7D32;
        font-weight: bold;
        font-style: italic;
        margin: 10px 0;
    }

    /* Form inputs with better contrast */
    .stTextInput input, .stSelectbox div [data-baseweb="select"] div {
        background-color: #ffffff;
        color: #1e1e1e;
        border: 1px solid #4CAF50;
        border-radius: 5px;
    }

    /* Placeholder text */
    .stTextInput input::placeholder {
        color: #9e9e9e;
    }

    /* Custom input field */
    .custom-input {
        background-color: #ffffff;
        border: 1px solid #4CAF50;
        border-radius: 5px;
        padding: 10px;
        color: #1e1e1e;
        width: 100%;
    }

    /* Story save notification */
    .save-notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #4CAF50;
        color: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: fadeIn 0.5s, fadeOut 0.5s 2.5s forwards;
    }

    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }

    @keyframes fadeOut {
        from {opacity: 1;}
        to {opacity: 0;}
    }

    /* Character card */
    .character-card {
        background-color: #ffffff;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        margin: 15px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Story options styling */
    .story-option {
        background-color: #ffffff;
        border-radius: 10px;
        border-left: 4px solid #673ab7;
        padding: 15px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        color: #1e1e1e;
    }

    .story-option:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Audio player styling */
    audio {
        width: 100%;
        margin: 10px 0;
        border-radius: 30px;
        background-color: #e8f5e9;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #e8f5e9;
    }
    
    /* Text in sidebar */
    .css-1d391kg p, .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: #1e1e1e;
    }
    </style>
    """, unsafe_allow_html=True)

# Load CSS
load_css()

# Helper function to generate content with Gemini
def generate_with_gemini(prompt, temperature=0.7, max_retries=3, retry_delay=2):
    attempt = 0
    while attempt < max_retries:
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                st.error(f"Error generating content after {max_retries} attempts: {str(e)}")
                return "Once upon a time, there was an error in the storytelling machine..."

# Parse JSON safely
def safe_json_parse(text):
    # First try direct parsing
    try:
        return json.loads(text)
    except:
        # Try to find JSON array in the text using regex
        json_match = re.search(r'\[\s*".*"\s*\]', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        # Try to extract items with quotes
        items = re.findall(r'"([^"]*)"', text)
        if items and len(items) > 0:
            return items
        
        # Fallback: split by newlines, numbers or bullets
        fallback_items = re.split(r'\n\s*(?:\d+\.|\*)\s*', text)
        fallback_items = [s.strip() for s in fallback_items if s.strip()]
        return fallback_items

# Function to clean story text by removing embedded AI choices
def clean_story_text(text):
    # Remove patterns like "Option A: ...", "1. ...", "Choice: ..." etc.
    patterns = [
        r'(?:Option|Choice)\s+[A-Za-z0-9]+\s*:\s*.*?(?=(?:Option|Choice)|$)',
        r'\d+\.\s+.*?(?=\d+\.|$)',
        r'•\s+.*?(?=•|$)'
    ]
    
    cleaned_text = text
    for pattern in patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL)
    
    # Remove any remaining numbered list markers
    cleaned_text = re.sub(r'^\s*\d+\.\s+', '', cleaned_text, flags=re.MULTILINE)
    
    # Remove any "What will you do?" or similar prompts
    prompts_to_remove = [
        r'What will you do\?',
        r'What do you do next\?',
        r'What happens next\?',
        r'What choice will you make\?',
        r'Choose your next action.',
        r'What would you like to do\?'
    ]
    
    for prompt in prompts_to_remove:
        cleaned_text = re.sub(prompt, '', cleaned_text)
    
    return cleaned_text.strip()

# Generate story starters based on genre
def generate_story_starters(genre=None, character_name=None):
    prompt = """
    Generate 3 unique and engaging story starters for an interactive fiction game.
    Each starter should be 2-3 sentences long and end with an intriguing situation that sets up a choice,
    but DO NOT include the choices in the starter.
    """
    
    if genre:
        prompt += f" The genre is {genre}."
        
    if character_name:
        prompt += f" The main character's name is {character_name}."
        
    prompt += """
    Make each starter distinct and compelling. Format the response as a JSON array with each starter as a string element.
    Example format: ["Starter 1...", "Starter 2...", "Starter 3..."]
    
    DO NOT include any choices or options in the starters themselves.
    """
    
    try:
        response = generate_with_gemini(prompt)
        starters = safe_json_parse(response)
        return starters[:3]  # Ensure we only return 3 starters
        
    except Exception as e:
        st.error(f"Error generating story starters: {str(e)}")
        return [
            f"You find yourself standing at the edge of a mysterious forest with a map that seems to lead to a hidden treasure.",
            f"The spaceship's alarm blares as you wake up from cryosleep, the rest of the crew is missing.",
            f"The old mansion you just inherited contains a locked room that nobody has entered for over a century."
        ]

# Generate choices for the user
def generate_choices(story_so_far, genre, character_name, num_choices=3):
    # First clean the story text to remove any embedded choices
    cleaned_story = clean_story_text(story_so_far)
    
    prompt = f"""
    Based on this story so far in the {genre} genre:
    
    {cleaned_story}
    
    Generate exactly {num_choices} interesting and distinct choices for what the character {character_name if character_name else 'the protagonist'} could do next.
    
    Each choice should:
    1. Be 1-2 sentences long
    2. Offer a clear and specific action
    3. Lead to different possible story directions
    4. Make sense given the current story situation
    5. NOT reference any options or choices that might be in the story text
    
    Format the response as a JSON array with each choice as a string element.
    Example format: ["Choice 1...", "Choice 2...", "Choice 3..."]
    
    IMPORTANT: DO NOT number the choices or add prefixes like "Option A" - just provide the plain choice text.
    """
    
    try:
        response = generate_with_gemini(prompt)
        choices = safe_json_parse(response)
        
        # Ensure we have the requested number of choices
        while len(choices) < num_choices:
            choices.append(f"Try something unexpected.")
            
        return choices[:num_choices]  # Return only the requested number of choices
        
    except Exception as e:
        st.error(f"Error generating choices: {str(e)}")
        return [
            "Continue forward cautiously.",
            "Turn back and seek another path.",
            "Call out to see if anyone responds."
        ]

# Continue the story based on user choice
def continue_story(story_so_far, chosen_action, genre, character_name):
    # Clean the story text first
    cleaned_story = clean_story_text(story_so_far)
    
    prompt = f"""
    Continue this {genre} story where the main character named {character_name if character_name else 'the protagonist'} has chosen the following action:
    
    Story so far: {cleaned_story}
    
    Chosen action: {chosen_action}
    
    Write the next part of the story (about 150-200 words) that follows from this choice. End at a natural stopping point that creates anticipation for what might happen next.
    
    IMPORTANT:
    - DO NOT include any numbered choices, options, or decision points in your response
    - DO NOT end with phrases like "What will you do?" or "What happens next?"
    - DO NOT write anything like "Option A:" or "Choice 1:" in your response
    - Focus on vivid descriptions, character emotions, and advancing the plot
    - Use a mix of narration and dialog where appropriate
    """
    
    response = generate_with_gemini(prompt, temperature=0.8)
    
    return clean_story_text(response)

# Generate a story ending
def generate_story_ending(story_so_far, genre, character_name):
    # Clean the story text first
    cleaned_story = clean_story_text(story_so_far)
    
    prompt = f"""
    Write a satisfying conclusion to this {genre} story featuring {character_name if character_name else 'the protagonist'}:
    
    {cleaned_story}
    
    Create a meaningful and emotionally resonant ending (about 200-300 words) that:
    1. Resolves the main tension or conflict
    2. Provides closure for the character
    3. Reflects the tone and themes of the {genre} genre
    4. Leaves the reader with a final image or thought
    
    Make the ending feel earned and connected to the character's journey.
    """
    
    return generate_with_gemini(prompt, temperature=0.8)

# Generate story recap
def generate_recap(story_state):
    choices_made = story_state["choices_made"]
    genre = story_state["genre"]
    character_name = story_state["character_name"] if story_state["character_name"] else "the protagonist"
    
    # If no choices made yet, return empty string
    if not choices_made:
        return ""
        
    prompt = f"""
    Create a brief recap (2-3 sentences) of this {genre} story so far featuring {character_name}.
    Focus on the key decisions and turning points.
    
    Here are the choices that were made: {', '.join(choices_made)}
    """
    
    recap = generate_with_gemini(prompt, temperature=0.7)
    
    return recap

# Save story to file
def save_story(story_state):
    story_id = story_state["story_id"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"saved_stories/{story_id}_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(story_state, f, indent=2)
        
    return filename

# Load saved stories list
def get_saved_stories():
    if not os.path.exists("saved_stories"):
        return []
        
    stories = []
    for filename in os.listdir("saved_stories"):
        if filename.endswith(".json"):
            file_path = os.path.join("saved_stories", filename)
            try:
                with open(file_path, "r") as f:
                    story_data = json.load(f)
                    
                # Extract key information
                story_info = {
                    "filename": filename,
                    "date": datetime.strptime(filename.split("_")[1].split(".")[0], "%Y%m%d%H%M%S").strftime("%b %d, %Y"),
                    "genre": story_data.get("genre", "Unknown"),
                    "character": story_data.get("character_name", "Unknown"),
                    "choices": len(story_data.get("choices_made", [])),
                    "story_id": story_data.get("story_id", "")
                }
                stories.append(story_info)
            except:
                pass
                
    # Sort by date (newest first)
    stories.sort(key=lambda x: x["date"], reverse=True)
    return stories

# Calculate story statistics
def calculate_story_stats(story_state):
    # Count words in current story
    word_count = len(story_state["current_text"].split())
    
    # Estimate reading time (avg 200-250 wpm)
    reading_time = round(word_count / 225)
    if reading_time < 1:
        reading_time = "< 1"
        
    # Count choices made
    choices_made = len(story_state["choices_made"])
    
    return {
        "word_count": word_count,
        "reading_time": reading_time,
        "choices_made": choices_made,
        "story_turns": story_state["story_turns"]
    }

# Welcome screen
def show_welcome():
    st.markdown("<h1 class='welcome-header'>Tale Weaver</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Interactive Story Generator</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="story-text">
        Welcome to Tale Weaver, where your choices shape the story! Each decision you make will lead to new adventures and unexpected twists.
        
        <h3>How to Play:</h3>
        1. Select a genre and customize your character
        2. Choose your starting scenario
        3. Make decisions at key points to guide the narrative
        4. Save your favorite stories to revisit later
        
        Every journey is different, and the possibilities are endless!
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Begin Your Journey", key="begin_journey", help="Start a new adventure"):
            st.session_state.story_state["stage"] = "setup"
            st.experimental_rerun()
            
    with col2:
        if st.button("Load Saved Story", key="load_saved", help="Continue a previous adventure"):
            st.session_state.view_saved = True
            st.experimental_rerun()
            
    # Show saved stories if requested
    if "view_saved" in st.session_state and st.session_state.view_saved:
        saved_stories = get_saved_stories()
        
        if not saved_stories:
            st.info("No saved stories found. Start a new adventure!")
            st.session_state.view_saved = False
        else:
            st.markdown("<h3 class='section-header'>Your Saved Adventures</h3>", unsafe_allow_html=True)
            
            for story in saved_stories:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    <div class="story-option">
                        <strong>{story['character']}'s {story['genre']} Adventure</strong><br>
                        <small>Saved on {story['date']} • {story['choices']} choices made</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col2:
                    if st.button("Continue", key=f"load_{story['story_id']}"):
                        file_path = os.path.join("saved_stories", story["filename"])
                        with open(file_path, "r") as f:
                            st.session_state.story_state = json.load(f)
                        st.session_state.story_state["stage"] = "story"
                        
                        # Clear any temporary states
                        if "view_saved" in st.session_state:
                            del st.session_state.view_saved
                        if "current_choices" in st.session_state:
                            del st.session_state.current_choices
                            
                        st.experimental_rerun()

# Setup screen
def show_setup():
    st.markdown("<h2 class='section-header'>Create Your Adventure</h2>", unsafe_allow_html=True)
    
    # Genre selection with color-coded badges
    st.markdown("<p>Select the type of story you want to experience:</p>", unsafe_allow_html=True)
    
    genre_options = {
        "Fantasy": "Magical worlds, mythical creatures, and heroic quests",
        "Science Fiction": "Future technology, space exploration, and scientific possibilities",
        "Mystery": "Puzzles, investigations, and secrets waiting to be uncovered",
        "Adventure": "Exploration, discovery, and overcoming challenges",
        "Horror": "Fear, suspense, and encounters with the unknown",
        "Romance": "Relationships, emotional connections, and matters of the heart",
        "Historical": "Stories set in the past, often based on real events or periods",
        "Comedy": "Humor, wit, and light-hearted situations"
    }
    
    # Create genre selection grid
    cols = st.columns(2)
    for i, (genre, description) in enumerate(genre_options.items()):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="story-option" id="genre-{genre.lower().replace(' ', '-')}">
                <span class="genre-badge">{genre}</span><br>
                <small>{description}</small>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Select {genre}", key=f"genre_{genre}"):
                st.session_state.selected_genre = genre
                
    # Show character creation after genre selection
    if "selected_genre" in st.session_state:
        st.markdown("<h3 class='section-header'>Create Your Character</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            character_name = st.text_input("Name your protagonist:", placeholder="Enter a name...", help="Leave blank for a nameless protagonist")
            
        with col2:
            character_trait = st.selectbox("Character's defining trait:", ["Brave", "Clever", "Cautious", "Curious", "Determined", "Witty", "Resourceful", "Compassionate", "Mysterious", "Practical"])
            
        # Generate story starters
        if st.button("Generate Story Beginnings", key="gen_starters"):
            with st.spinner("Crafting your adventure beginnings..."):
                starters = generate_story_starters(st.session_state.selected_genre, character_name)
                st.session_state.story_starters = starters
                st.session_state.character_trait = character_trait
                
        # Show starters if available
        if "story_starters" in st.session_state and "selected_genre" in st.session_state:
            st.markdown("<h3 class='section-header'>Choose your starting point:</h3>", unsafe_allow_html=True)
            
            for i, starter in enumerate(st.session_state.story_starters):
                st.markdown(f"""
                <div class="story-option">
                    {starter}
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Begin This Story", key=f"starter_{i}"):
                    # Save selections and move to story stage
                    st.session_state.story_state["genre"] = st.session_state.selected_genre
                    st.session_state.story_state["character_name"] = character_name if 'character_name' in locals() else ""
                    st.session_state.story_state["character_trait"] = st.session_state.character_trait
                    st.session_state.story_state["current_text"] = starter
                    st.session_state.story_state["stage"] = "story"
                    st.session_state.story_state["path_taken"].append({"type": "beginning", "text": starter})
                    st.session_state.story_state["word_count"] = len(starter.split())
                    st.session_state.story_state["story_turns"] = 0
                    
                    # Generate audio for the starter
                    audio_path = text_to_speech(starter)
                    if audio_path:
                        st.session_state.current_audio = audio_path
                    
                    # Clear temporary states
                    if "current_choices" in st.session_state:
                        del st.session_state.current_choices
                        
                    st.experimental_rerun()

# Story screen
def show_story():
    # Story header with genre badge
    st.markdown(f"""
    <h2 class='section-header'>
        <span class='genre-badge'>{st.session_state.story_state['genre']}</span> 
        {st.session_state.story_state['character_name'] + "'s" if st.session_state.story_state['character_name'] else "Your"} Adventure
    </h2>
    """, unsafe_allow_html=True)
    
    # Story statistics
    stats = calculate_story_stats(st.session_state.story_state)
    st.markdown(f"""
    <div class='progress-indicator'>
        <strong>Story Progress:</strong> Turn {stats['story_turns']} | 
        <strong>Words:</strong> {stats['word_count']} | 
        <strong>Reading Time:</strong> ~{stats['reading_time']} min | 
        <strong>Choices Made:</strong> {stats['choices_made']}
    </div>
    """, unsafe_allow_html=True)
    
    # Format and display current story with improved styling
    formatted_story = st.session_state.story_state["current_text"]
    
    # Process for better display - convert dialog
    formatted_story = re.sub(r'"([^"]*)"', r'<span class="dialog">"\1"</span>', formatted_story)
    
    st.markdown(f"<div class='story-text'>{formatted_story}</div>", unsafe_allow_html=True)
    
    # Play audio if available
    if "current_audio" in st.session_state:
        audio_player = get_audio_player_html(st.session_state.current_audio)
        st.markdown(audio_player, unsafe_allow_html=True)
        # Remove the reference after playing
        del st.session_state.current_audio
    
    # Generate choices if not already present
    if "current_choices" not in st.session_state:
        with st.spinner("Determining possible paths..."):
            choices = generate_choices(
                st.session_state.story_state["current_text"],
                st.session_state.story_state["genre"],
                st.session_state.story_state["character_name"]
            )
            st.session_state.current_choices = choices
    
    # Display choices
    st.markdown("<h3>What will you do next?</h3>", unsafe_allow_html=True)
    
    for i, choice in enumerate(st.session_state.current_choices):
        if st.button(choice, key=f"choice_{i}", help="Choose this action"):
            chosen_action = choice
            
            # Record choice
            st.session_state.story_state["choices_made"].append(chosen_action)
            st.session_state.story_state["path_taken"].append({"type": "choice", "text": chosen_action})
            
            # Continue story based on choice
            with st.spinner("The story unfolds..."):
                next_part = continue_story(
                    st.session_state.story_state["current_text"],
                    chosen_action,
                    st.session_state.story_state["genre"],
                    st.session_state.story_state["character_name"])
                
                # Update story text with user's choice and next part
                st.session_state.story_state["current_text"] += f"\n\n<div class='choice-marker'>You chose: {chosen_action}</div>\n\n{next_part}"
                
                # Generate audio for the next part
                audio_path = text_to_speech(next_part)
                if audio_path:
                    st.session_state.current_audio = audio_path
                
                # Update word count
                st.session_state.story_state["word_count"] = len(st.session_state.story_state["current_text"].split())
                
                # Increment turn counter
                st.session_state.story_state["story_turns"] += 1
                
                # Save automatically
                save_story(st.session_state.story_state)
                
                # Check if we should end story based on turns
                if st.session_state.story_state["story_turns"] >= 10:
                    st.session_state.story_state["stage"] = "ending"
                
                # Clear choices for next turn
                if "current_choices" in st.session_state:
                    del st.session_state.current_choices
                    
                st.experimental_rerun()
    
    # Navigation options
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Save Story", key="save_story_button"):
            filename = save_story(st.session_state.story_state)
            st.success(f"Story saved successfully!")
            
    with col2:
        if st.button("End Story", key="end_story_button"):
            st.session_state.story_state["stage"] = "ending"
            st.experimental_rerun()
            
    with col3:
        if st.button("New Story", key="new_story_button"):
            if st.session_state.story_state["story_turns"] > 0:
                # Save current story before starting new
                save_story(st.session_state.story_state)
                
            # Reset story state
            st.session_state.story_state = {
                "story_id": str(uuid.uuid4()),
                "current_text": "",
                "choices_made": [],
                "path_taken": [],
                "genre": "",
                "character_name": "",
                "stage": "welcome",
                "story_turns": 0,
                "word_count": 0
            }
            
            # Clear any temporary states
            if "current_choices" in st.session_state:
                del st.session_state.current_choices
            if "selected_genre" in st.session_state:
                del st.session_state.selected_genre
            if "story_starters" in st.session_state:
                del st.session_state.story_starters
            if "current_audio" in st.session_state:
                del st.session_state.current_audio
                
            st.experimental_rerun()

# Story ending screen
def show_ending():
    st.markdown("<h2 class='section-header'>Story Conclusion</h2>", unsafe_allow_html=True)
    
    if "ending_text" not in st.session_state:
        with st.spinner("Crafting your story's conclusion..."):
            ending = generate_story_ending(
                st.session_state.story_state["current_text"],
                st.session_state.story_state["genre"],
                st.session_state.story_state["character_name"]
            )
            st.session_state.ending_text = ending
            
            # Generate audio for the ending
            audio_path = text_to_speech(ending)
            if audio_path:
                st.session_state.ending_audio = audio_path
    
    # Update story with ending
    st.session_state.story_state["current_text"] += f"\n\n<div class='section-header'>The Conclusion</div>\n\n{st.session_state.ending_text}"
    st.session_state.story_state["path_taken"].append({"type": "ending", "text": st.session_state.ending_text})
    
    # Update word count
    st.session_state.story_state["word_count"] = len(st.session_state.story_state["current_text"].split())
    
    # Save story with ending
    save_story(st.session_state.story_state)
    
    # Display story stats
    stats = calculate_story_stats(st.session_state.story_state)
    
    st.markdown(f"""
    <div class='progress-indicator'>
        <strong>Final Statistics:</strong><br>
        <strong>Story Length:</strong> {stats['word_count']} words<br>
        <strong>Reading Time:</strong> ~{stats['reading_time']} minutes<br>
        <strong>Choices Made:</strong> {stats['choices_made']}<br>
        <strong>Story Turns:</strong> {stats['story_turns']}
    </div>
    """, unsafe_allow_html=True)
    
    # Play ending audio if available
    if "ending_audio" in st.session_state:
        audio_player = get_audio_player_html(st.session_state.ending_audio)
        st.markdown(audio_player, unsafe_allow_html=True)
        # Remove the reference after playing
        del st.session_state.ending_audio
    
    # Generate and display summary/recap
    with st.expander("Your Adventure Summary", expanded=True):
        recap = generate_recap(st.session_state.story_state)
        st.markdown(f"<div class='story-text'>{recap}</div>", unsafe_allow_html=True)
    
    # Display full story with ending
    with st.expander("Read Your Complete Story", expanded=True):
        formatted_story = st.session_state.story_state["current_text"]
        # Process for better display - convert dialog
        formatted_story = re.sub(r'"([^"]*)"', r'<span class="dialog">"\1"</span>', formatted_story)
        st.markdown(f"<div class='story-text'>{formatted_story}</div>", unsafe_allow_html=True)
    
    # Options for next steps
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start New Adventure", key="new_adventure"):
            # Reset story state
            st.session_state.story_state = {
                "story_id": str(uuid.uuid4()),
                "current_text": "",
                "choices_made": [],
                "path_taken": [],
                "genre": "",
                "character_name": "",
                "stage": "welcome",
                "story_turns": 0,
                "word_count": 0
            }
            
            # Clear temporary states
            if "current_choices" in st.session_state:
                del st.session_state.current_choices
            if "selected_genre" in st.session_state:
                del st.session_state.selected_genre
            if "story_starters" in st.session_state:
                del st.session_state.story_starters
            if "ending_text" in st.session_state:
                del st.session_state.ending_text
                
            st.experimental_rerun()
    
    with col2:
        if st.button("Browse Saved Stories", key="view_saved_stories"):
            # Reset story state but keep saved stories
            st.session_state.story_state = {
                "story_id": str(uuid.uuid4()),
                "current_text": "",
                "choices_made": [],
                "path_taken": [],
                "genre": "",
                "character_name": "",
                "stage": "welcome",
                "story_turns": 0,
                "word_count": 0
            }
            
            # Set flag to view saved stories
            st.session_state.view_saved = True
            
            # Clear temporary states
            if "current_choices" in st.session_state:
                del st.session_state.current_choices
            if "selected_genre" in st.session_state:
                del st.session_state.selected_genre
            if "story_starters" in st.session_state:
                del st.session_state.story_starters
            if "ending_text" in st.session_state:
                del st.session_state.ending_text
                
            st.experimental_rerun()
    
    # Export options
    st.markdown("<h3 class='section-header'>Export Your Story</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Copy to Clipboard", key="copy_clipboard"):
            clean_text = re.sub(r'<[^>]*>', '', st.session_state.story_state["current_text"])
            st.code(clean_text, language=None)
            st.success("Text copied! Use Ctrl+C or Cmd+C to copy from the box above.")
    
    with col2:
        # Generate download link for text file
        clean_text = re.sub(r'<[^>]*>', '', st.session_state.story_state["current_text"])
        st.download_button(
            label="Download as Text File",
            data=clean_text,
            file_name=f"{st.session_state.story_state['genre']}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            key="download_text"
        )

# Sidebar content
def show_sidebar():
    st.sidebar.markdown("## Tale Weaver")
    st.sidebar.markdown("An interactive storytelling experience powered by AI")
    
    # Show current story info if in story mode
    if st.session_state.story_state["stage"] in ["story", "ending"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Your Adventure")
        
        if st.session_state.story_state["genre"]:
            st.sidebar.markdown(f"*Genre:* {st.session_state.story_state['genre']}")
            
        if st.session_state.story_state["character_name"]:
            st.sidebar.markdown(f"*Protagonist:* {st.session_state.story_state['character_name']}")
            
        # Show choices made
        if st.session_state.story_state["choices_made"]:
            with st.sidebar.expander("Your Journey So Far", expanded=False):
                for i, choice in enumerate(st.session_state.story_state["choices_made"]):
                    st.sidebar.markdown(f"{i+1}. {choice}")
    
    # Tips and information
    st.sidebar.markdown("---")
    with st.sidebar.expander("📝 Story Tips", expanded=False):
        st.markdown("""
        - Your choices influence the story direction
        - Stories automatically save after each choice
        - Aim for 7-10 choices for a complete story arc
        - Each genre has different storytelling styles
        - Character traits subtly influence story events
        """)
    
    # Credits
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Credits")
    st.sidebar.markdown("Created with Streamlit and Gemini API")
    st.sidebar.markdown("© 2025 Tale Weaver")

# Main app flow
def main():
    # Load CSS
    load_css()
    
    # Show sidebar
    show_sidebar()
    
    # Determine which screen to show based on story stage
    if st.session_state.story_state["stage"] == "welcome":
        show_welcome()
    elif st.session_state.story_state["stage"] == "setup":
        show_setup()
    elif st.session_state.story_state["stage"] == "story":
        show_story()
    elif st.session_state.story_state["stage"] == "ending":
        show_ending()

if __name__ == "__main__":
    main()

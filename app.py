import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import uuid
import time
from datetime import datetime

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

# Initialize or load session state
if "story_state" not in st.session_state:
    st.session_state.story_state = {
        "story_id": str(uuid.uuid4()),
        "current_text": "",
        "choices_made": [],
        "path_taken": [],
        "genre": "",
        "character_name": "",
        "stage": "welcome"  # welcome, setup, story, ending
    }

# Custom styling with improved contrast and button overrides
def load_css():
    st.markdown("""
    <style>
        /* Background and overall text color */
        .stApp {
            background-image: linear-gradient(to bottom, #1e3c72, #2a5298);
            color: #ffffff;
        }
        /* Story text container with a darker transparent background */
        .story-text {
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            line-height: 1.6;
            color: #ffffff;
        }
        /* Override default Streamlit button styling for better contrast */
        .stButton button {
            background-color: #4CAF50;
            color: #ffffff;
            padding: 10px 24px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            transition: background-color 0.3s ease;
        }
        .stButton button:hover {
            background-color: #3e8e41;
        }
        /* Sidebar button styling (optional customization) */
        .sidebar .stButton button {
            background-color: #6a1b9a;
        }
        /* Headers with text shadow for clarity */
        .welcome-header {
            font-size: 4rem;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px #000000;
            color: #ffffff;
        }
        .section-header {
            font-size: 2rem;
            margin-top: 20px;
            margin-bottom: 10px;
            text-shadow: 1px 1px 2px #000000;
            color: #ffffff;
        }
    </style>
    """, unsafe_allow_html=True)

# Load CSS
load_css()

# Helper function to generate content with Gemini
def generate_with_gemini(prompt, temperature=0.7):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating content: {str(e)}")
        return "Once upon a time, there was an error in the storytelling machine..."

# Generate story starters based on genre
def generate_story_starters(genre=None):
    prompt = """
    Generate 3 unique and engaging story starters for an interactive fiction game. 
    Each starter should be 2-3 sentences long and end with an intriguing hook or question.
    """
    
    if genre:
        prompt += f" The genre is {genre}."
    
    prompt += """
    Format the response as a JSON array with each starter as a string element.
    Example format: ["Starter 1...", "Starter 2...", "Starter 3..."]
    """
    
    try:
        response = generate_with_gemini(prompt)
        # Try to parse as JSON
        try:
            starters = json.loads(response)
            if isinstance(starters, list):
                return starters
        except:
            # If parsing fails, try to extract the JSON part
            import re
            json_match = re.search(r'\[\s*".*"\s*\]', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
        
        # Fallback: split by newlines and clean up
        fallback_starters = response.split('\n')
        fallback_starters = [s.strip() for s in fallback_starters if s.strip()]
        fallback_starters = [s.strip('"').strip() for s in fallback_starters]
        return fallback_starters[:3]
    
    except Exception as e:
        st.error(f"Error generating story starters: {str(e)}")
        return [
            "You find yourself standing at the edge of a mysterious forest with a map that seems to lead to a hidden treasure.",
            "The spaceship's alarm blares as you wake up from cryosleep, the rest of the crew is missing.",
            "The old mansion you just inherited contains a locked room that nobody has entered for over a century."
        ]

# Generate choices for the user
def generate_choices(story_so_far, genre, character_name):
    prompt = f"""
    Based on this story so far in the {genre} genre:
    
    {story_so_far}
    
    Generate 3 interesting and distinct choices for what could happen next, each about 1 sentence long.
    Format the response as a JSON array with each choice as a string element.
    Example format: ["Choice 1...", "Choice 2...", "Choice 3..."]
    """
    
    try:
        response = generate_with_gemini(prompt)
        try:
            choices = json.loads(response)
            if isinstance(choices, list):
                return choices
        except:
            # If parsing fails, try to extract the JSON part
            import re
            json_match = re.search(r'\[\s*".*"\s*\]', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
        
        # Fallback: split by newlines and clean up
        fallback_choices = response.split('\n')
        fallback_choices = [s.strip() for s in fallback_choices if s.strip()]
        fallback_choices = [s.strip('"').strip() for s in fallback_choices]
        return fallback_choices[:3]
    
    except Exception as e:
        st.error(f"Error generating choices: {str(e)}")
        return [
            "Continue forward cautiously.",
            "Turn back and seek another path.",
            "Call out to see if anyone responds."
        ]

# Continue the story based on user choice
def continue_story(story_so_far, chosen_action, genre, character_name):
    prompt = f"""
    Continue this {genre} story where the main character named {character_name if character_name else 'the protagonist'} has chosen the following action:
    
    Story so far: {story_so_far}
    
    Chosen action: {chosen_action}
    
    Write the next part of the story (about 150-200 words) that follows from this choice. 
    End at another decision point or cliffhanger that will lead to new choices.
    """
    
    return generate_with_gemini(prompt, temperature=0.8)

# Save story to file
def save_story(story_state):
    story_id = story_state["story_id"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"saved_stories/{story_id}_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(story_state, f, indent=2)
    
    return filename

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
    
    if st.button("Begin Your Journey", key="begin_journey"):
        st.session_state.story_state["stage"] = "setup"
        st.experimental_rerun()

# Setup screen
def show_setup():
    st.markdown("<h2 class='section-header'>Create Your Adventure</h2>", unsafe_allow_html=True)
    
    # Genre selection
    genre_options = ["Fantasy", "Science Fiction", "Mystery", "Adventure", "Horror", "Romance", "Historical", "Comedy"]
    selected_genre = st.selectbox("Choose your story genre:", genre_options)
    
    # Character name
    character_name = st.text_input("Name your protagonist (optional):")
    
    # Generate story starters
    if st.button("Generate Story Starters"):
        with st.spinner("Crafting your adventure beginnings..."):
            starters = generate_story_starters(selected_genre)
            st.session_state.story_starters = starters
    
    # Show starters if available
    if "story_starters" in st.session_state:
        st.markdown("<h3>Choose your starting point:</h3>", unsafe_allow_html=True)
        
        for i, starter in enumerate(st.session_state.story_starters):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"<div class='story-text'>{starter}</div>", unsafe_allow_html=True)
            with col2:
                if st.button(f"Select", key=f"starter_{i}"):
                    # Save selections and move to story stage
                    st.session_state.story_state["genre"] = selected_genre
                    st.session_state.story_state["character_name"] = character_name
                    st.session_state.story_state["current_text"] = starter
                    st.session_state.story_state["stage"] = "story"
                    st.session_state.story_state["path_taken"].append({"type": "beginning", "text": starter})
                    st.experimental_rerun()

# Story screen
def show_story():
    st.markdown("<h2 class='section-header'>Your Adventure</h2>", unsafe_allow_html=True)
    
    # Display current story
    st.markdown(f"<div class='story-text'>{st.session_state.story_state['current_text']}</div>", unsafe_allow_html=True)
    
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
        if st.button(choice, key=f"choice_{i}"):
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
                    st.session_state.story_state["character_name"]
                )
                
                # Update story state
                st.session_state.story_state["current_text"] += f"\n\n[You chose: {chosen_action}]\n\n{next_part}"
                st.session_state.story_state["path_taken"].append({"type": "story", "text": next_part})
                
                # Clear choices for next round
                if "current_choices" in st.session_state:
                    del st.session_state.current_choices
                
                st.experimental_rerun()
    
    # Option to end and save story
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Story"):
            filename = save_story(st.session_state.story_state)
            st.success("Story saved successfully!")
    
    with col2:
        if st.button("End Story & Start New"):
            if "current_choices" in st.session_state:
                del st.session_state.current_choices
            if "story_starters" in st.session_state:
                del st.session_state.story_starters
            
            # Reset story state
            st.session_state.story_state = {
                "story_id": str(uuid.uuid4()),
                "current_text": "",
                "choices_made": [],
                "path_taken": [],
                "genre": "",
                "character_name": "",
                "stage": "welcome"
            }
            st.experimental_rerun()

# Custom user input (for future enhancement)
def process_custom_input():
    user_input = st.text_input("Or type your own action:")
    if user_input and st.button("Submit Custom Action"):
        # Record custom choice
        st.session_state.story_state["choices_made"].append(user_input)
        st.session_state.story_state["path_taken"].append({"type": "custom_choice", "text": user_input})
        
        # Continue story based on custom input
        with st.spinner("The story unfolds based on your action..."):
            next_part = continue_story(
                st.session_state.story_state["current_text"],
                user_input,
                st.session_state.story_state["genre"],
                st.session_state.story_state["character_name"]
            )
            
            # Update story state
            st.session_state.story_state["current_text"] += f"\n\n[You decided to: {user_input}]\n\n{next_part}"
            st.session_state.story_state["path_taken"].append({"type": "story", "text": next_part})
            
            # Clear choices for next round
            if "current_choices" in st.session_state:
                del st.session_state.current_choices
            
            st.experimental_rerun()

# Main app flow
def main():
    # Side navigation for logged stories and settings
    with st.sidebar:
        st.markdown("# 📚 Tale Weaver")
        st.markdown("---")
        
        if st.session_state.story_state["stage"] == "story":
            st.markdown(f"**Genre:** {st.session_state.story_state['genre']}")
            if st.session_state.story_state["character_name"]:
                st.markdown(f"**Protagonist:** {st.session_state.story_state['character_name']}")
            st.markdown(f"**Choices made:** {len(st.session_state.story_state['choices_made'])}")
            
            st.markdown("---")
            if st.button("Start Over"):
                if "current_choices" in st.session_state:
                    del st.session_state.current_choices
                if "story_starters" in st.session_state:
                    del st.session_state.story_starters
                
                # Reset story state
                st.session_state.story_state = {
                    "story_id": str(uuid.uuid4()),
                    "current_text": "",
                    "choices_made": [],
                    "path_taken": [],
                    "genre": "",
                    "character_name": "",
                    "stage": "welcome"
                }
                st.experimental_rerun()
    
    # Main content area
    if st.session_state.story_state["stage"] == "welcome":
        show_welcome()
    elif st.session_state.story_state["stage"] == "setup":
        show_setup()
    elif st.session_state.story_state["stage"] == "story":
        show_story()

if __name__ == "__main__":
    main()

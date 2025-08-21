import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import warnings
import logging
from dotenv import load_dotenv

# --- ADK Core Imports ---
from google.adk.agents import LlmAgent
from google.adk.tools import google_search # import google search tool
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types as genai_types # For creating message Content/Parts

# --- Our Custom Tools ---
from tools.movie_searcher import get_top_movies
from tools.social_poster import download_movie_posters

# --- Initial Setup ---
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)
load_dotenv()

# --- Configure Environment and API Keys ---
# This setup uses Gemini directly via API Key, not Vertex AI.
#os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY is not set in the .env file. Please add it.")
    exit()

# Define Model Constant
MODEL_GEMINI_FLASH = "gemini-2.5-flash"

# download_movie_posters tool
def download_movie_posters(movie_titles: str) -> str:
    """
    Downloads movie posters using OMDb API for a list of movies.
    Saves posters in the 'output' directory.

    Args:
        movie_titles (str): Comma-separated list of movie titles to download posters for.

    Returns:
        str: Status message with details of downloaded posters.
    """
    print(f"--- Tool: download_movie_posters called ---")
    
    # Get API key from environment
    omdb_api_key = os.getenv("OMDB_API_KEY")
    if not omdb_api_key:
        return "Error: OMDB_API_KEY not found in environment variables."
    
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse movie titles
    titles = [title.strip() for title in movie_titles.split(',')]
    downloaded_posters = []
    failed_downloads = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for title in titles:
        try:
            print(f"Fetching poster for: {title}")
            
            # Call OMDb API to get movie data including poster URL
            api_url = f"https://www.omdbapi.com/?t={title}&apikey={omdb_api_key}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                movie_data = response.json()
                
                # Check if the API call was successful
                if movie_data.get('Response') == 'True':
                    poster_url = movie_data.get('Poster')
                    
                    if poster_url and poster_url != 'N/A':
                        print(f"Found poster URL: {poster_url}")
                        
                        try:
                            # Download the poster image
                            poster_response = requests.get(poster_url, headers=headers, timeout=15)
                            
                            if poster_response.status_code == 200:
                                # Create safe filename
                                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', title)
                                file_extension = '.jpg'
                                file_path = os.path.join(output_dir, f"{safe_filename}{file_extension}")
                                
                                # Save the poster
                                with open(file_path, 'wb') as f:
                                    f.write(poster_response.content)
                                
                                downloaded_posters.append(f"{title} -> {file_path}")
                                print(f"Downloaded: {title} -> {file_path}")
                                
                            else:
                                failed_downloads.append(f"{title} (HTTP {poster_response.status_code})")
                                print(f"Failed to download poster for {title}: HTTP {poster_response.status_code}")
                                
                        except Exception as e:
                            failed_downloads.append(f"{title} (Download error)")
                            print(f"Error downloading poster for {title}: {e}")
                    else:
                        failed_downloads.append(f"{title} (No poster URL)")
                        print(f"No poster URL found for: {title}")
                else:
                    error_msg = movie_data.get('Error', 'Unknown error')
                    failed_downloads.append(f"{title} (API error: {error_msg})")
                    print(f"OMDb API error for {title}: {error_msg}")
            else:
                failed_downloads.append(f"{title} (HTTP {response.status_code})")
                print(f"Failed to call OMDb API for {title}: HTTP {response.status_code}")
            
            # Add delay between requests to be respectful
            time.sleep(1)
            
        except Exception as e:
            failed_downloads.append(f"{title} (Exception)")
            print(f"Error processing {title}: {e}")
    
    # Prepare status message
    status_message = f"Poster Download Complete!\n\n"
    status_message += f"Successfully downloaded {len(downloaded_posters)} posters:\n"
    for poster in downloaded_posters:
        status_message += f"✓ {poster}\n"
    
    if failed_downloads:
        status_message += f"\nFailed to download {len(failed_downloads)} posters:\n"
        for failed in failed_downloads:
            status_message += f"✗ {failed}\n"
    
    status_message += f"\nAll posters saved in: {os.path.abspath(output_dir)}"
    
    return status_message

# --- 1. Define the Agent ---
# The instruction prompt is the most critical part. It tells the agent its
# goal and the exact sequence of steps to follow.
movie_agent = LlmAgent(
    name="movie_poster_agent_v1",
    model=MODEL_GEMINI_FLASH,
    description="A comprehensive movie recommendation agent that finds top-rated movies and downloads their posters using OMDb API.",
    instruction=(
        "You are a movie recommendation and poster download agent. When asked for movies of a specific genre, follow these steps:\n\n"
        "STEP 1: SEARCH FOR MOVIES\n"
        "- Use the get_top_movies tool to find the top 10 movies for the requested genre\n"
        "- This tool internally uses Google search to find real-time movie data\n\n"
        "STEP 2: PRESENT MOVIE LIST\n"
        "Present exactly 10 movies in this format:\n"
        "**TOP 10 [GENRE] MOVIES:**\n\n"
        "1. Movie Title (Year) - IMDb: X.X/10\n"
        "2. Movie Title (Year) - IMDb: X.X/10\n"
        "[Continue for all 10 movies]\n\n"
        "STEP 3: DOWNLOAD POSTERS\n"
        "After presenting the complete movie list, use the download_movie_posters tool with "
        "a comma-separated string of movie titles (e.g., 'Inception, The Matrix, Interstellar') "
        "to download posters using OMDb API and save them in the 'output' folder.\n\n"
        "You MUST complete ALL steps: search, present movie list, AND download posters."
    ),
    tools=[get_top_movies, google_search, download_movie_posters]
)
print(f"Agent '{movie_agent.name}' created using model '{MODEL_GEMINI_FLASH}'.")


# --- 2. Define Agent Interaction Function ---
async def call_agent_async(query: str, runner, user_id, session_id):
  """Sends a query to the agent and prints all events and the final response."""
  #print(f"\n>>> User Query: {query}")
  content = genai_types.Content(role='user', parts=[genai_types.Part(text=query)])
  final_response_text = "Agent did not produce a final response."

  # The runner executes the agent and yields events (thoughts, tool calls, final answer).
  event_count = 0
  async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
      """event_count += 1
      print(f"\n--- Event {event_count} ---")
      
      # Show event details
      if hasattr(event, 'content') and hasattr(event.content, 'parts'):
          for part in event.content.parts:
              if hasattr(part, 'text') and part.text:
                  print(part.text)"""
      
      # Check for final response
      if event.is_final_response():
          if event.content and event.content.parts:
             final_response_text = event.content.parts[0].text
          print(f"\n<<< Agent Final Response: {final_response_text}")
          break


# --- 3. Main Execution Block ---
async def main():
    # --- Setup Runner and Session Service ---
    session_service = InMemorySessionService()
    APP_NAME = "movie_poster_app"
    USER_ID = "user_v1"
    SESSION_ID = "session_v1"

    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    print(f"Session created for '{APP_NAME}'.")

    runner = Runner(agent=movie_agent, app_name=APP_NAME, session_service=session_service)
    print(f"Runner created for agent '{runner.agent.name}'.")
    print("Hello! Enter Your Query: ")

    # --- the interactive chat loop ---
    while True:
        #  Interact with the Agent 
        user_query = input(">>> User Query:") #"Please create and publish a post for the Sci-Fi genre."
        #check if the user wants to exit the session
        if user_query.lower() in ["exit", "quit", "q"]:
            print("Ending session, Goodbye!...")
            break

        await call_agent_async(user_query, runner, USER_ID, SESSION_ID)

if __name__ == "__main__":
    asyncio.run(main())
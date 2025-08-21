import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search # import google search tool
from movie_poster_agent.social_agent_tools import download_movie_posters, create_final_images


movie_search = LlmAgent(
    name = "movie_search_agent",
    model="gemini-2.5-flash",
    description="A comprehensive movie recommendation agent that finds top-rated movies",
    instruction =("You are a movie recommendation agent. When asked for movies of a specific genre, follow these steps:\n\n"
        "STEP 1: SEARCH FOR MOVIES\n"
        "- Use google_search tool with query: 'top 10 highest rated best [genre] movies from IMDb and imdb rating should be greater than 8.0 and imdbVotes>100000, sorted by their IMDb rating and popularity.'\n"
        "- Extract movie titles, years, and ratings from search results\n\n"
        "STEP 2: PRESENT MOVIE LIST\n"
        "Present exactly 10 movies in this format:\n"
        "**TOP 10 [GENRE] MOVIES:**\n\n"
        "1. Movie Title (Year) - IMDb: X.X/10\n"
        "2. Movie Title (Year) - IMDb: X.X/10\n"
        "[Continue for all 10 movies]\n\n"),
    tools=[google_search]
)

movie_agent = LlmAgent(
    name="movie_poster_agent_v1",
    model="gemini-2.5-flash",
    description="A comprehensive movie recommendation agent that finds top-rated movies and downloads their posters using OMDb API.",
    instruction=(
        "You are a movie recommendation and poster download agent. When asked for movies of a specific genre, follow these steps:\n\n"
        "STEP 1: SEARCH FOR MOVIES\n"
        "Use movie_search tool and pass the genre as an argument to get the top 10 movies for the requested genre\n"
        "STEP 2: DOWNLOAD POSTERS\n"
        "After presenting the complete movie list, use the download_movie_posters tool with "
        "pass the dictionary of movies, title as key with rating as value (e.g., {'Inception':'8.7', 'Interstellar':'8.7', 'The Matrix':'8.5'}) "
        "STEP 3: CREATE FINAL IMAGES\n"
        "After downloading the posters, use the create_final_images tool to create final images.\n"
        "Pass the folder path of downloaded posters from download_movie_posters tool and cover text as arguments to create_final_images tool.\n"
        "cover text should be creative and engaging. e.g if genre is action then cover text should be 'Top 10 Action Movies of All Time' \n"
        "You MUST complete ALL steps: movie_search, download_movie_posters, create_final_images."
    ),
    tools=[AgentTool(agent=movie_search), download_movie_posters, create_final_images]
)

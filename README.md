# movie_post_agent
An AI-powered movie recommendation and poster generation system that discovers top-rated films by genre, downloads their posters, and creates polished promotional images.

## Features
- Top 10 movies discovery per genre using Google Search (`google_search` tool)
- Poster download and validation via `download_movie_posters()`
- Automated image composition via `create_final_images()`
- Modular, tool-driven agents built on Google ADK `LlmAgent`
- Designed to be integrated into broader multi-agent workflows

## Architecture
- `agent.py`
  - Defines two agents:
    - `movie_search` – finds top-rated movies (title, year, rating) for a given genre via Google Search
    - `movie_agent` – orchestrates: search → download posters → create final images
  - Uses tools: `google_search`, and local `social_agent_tools`
- `social_agent_tools.py`
  - `download_movie_posters(movies: Dict[str,str]) -> str`: downloads posters for provided movies and returns the output folder path plus a status message
  - `create_final_images(raw_poster_folder: str, cover_text: str) -> List[str]`: processes raw posters into final edited images and returns the list of output file paths

## Prerequisites
- Python 3.10+
- Access to the Google ADK Agents framework and tools (e.g., `google.adk.agents`, `google.adk.tools`)
- (Optional) OMDb or other poster sources if you extend the tooling

## Setup
```bash
# clone your repo
git clone https://github.com/GedelaSuryaDev/movie_post_agent.git
cd movie_post_agent

# create & activate a virtual environment (example for Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install your dependencies (adapt if you manage deps elsewhere)
pip install -r requirements.txt  # if present
```

If your environment is managed outside this folder (e.g., monorepo with a root `pyproject.toml`), install from the project root accordingly.

## Configuration
- Add any required API keys or environment variables the tools may need (e.g., poster sources) via your standard method:
  - local `.env`
  - environment variables
  - secret manager

## Usage
Integrate the agents into your app or orchestrator. Example (pseudo-usage):

```python
from movie_poster_agent.agent import movie_agent

user_prompt = "Please fetch movies for the Sci-Fi genre"
# Depending on your ADK runtime, invoke the agent accordingly, e.g.:
# result = movie_agent.run(user_prompt)
# print(result)
```

The `movie_agent` will:
1) Use `movie_search` to return the top 10 movies for the requested genre
2) Call `download_movie_posters()` with a dict of movie → rating
3) Call `create_final_images()` to generate finished assets with an engaging cover title

Outputs include the folder path with downloaded posters and a list of final edited image paths.

## Development
- Lint/format as per your team standards
- Update `.gitignore` as needed (this repo ignores `__pycache__`, virtual envs, and build artifacts)

## Notes
- This package is designed to be embedded in multi-agent systems. If you are using a custom runner, adapt the agent invocation to your runtime’s API.
- If you do not want to track local scripts (e.g., experimental drivers), add them to `.gitignore`.


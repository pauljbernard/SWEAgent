import os
import google.generativeai as genai
from google.generativeai import caching
import google.api_core.exceptions as exceptions
import datetime
import requests
import subprocess
from pathlib import Path
from typing import Optional
import json
from urllib.parse import urlparse
import yaml
import time

import dotenv
import os

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


dotenv.load_dotenv()
CONTEXT_CACHING_RETRIVER = os.getenv("CONTEXT_CACHING_RETRIVER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Default configuration with environment variable
genai.configure(api_key=GEMINI_API_KEY)

# Function to configure API with a specific key
def configure_gemini_api(api_key=None):
    """Configure Gemini API with a specific key or use the environment variable"""
    if api_key:
        genai.configure(api_key=api_key)
    else:
        genai.configure(api_key=GEMINI_API_KEY)


def clone_github_repo(folder_path: str, repo_url: str) -> Optional[str]:
    """
    Clone a GitHub repository into a specified folder or return path if already cloned.

    Args:
        folder_path (str): The path where the repository should be cloned
        repo_url (str): The GitHub repository URL (e.g., 'https://github.com/username/repo')

    Returns:
        Optional[str]: The path to the cloned repository if successful, None if failed

    Raises:
        ValueError: If the inputs are invalid
        subprocess.CalledProcessError: If the git clone operation fails
    """
    # Validate inputs
    if not folder_path or not repo_url:
        raise ValueError("Both folder_path and repo_url must be provided")

    # Parse the repository URL to get the repository name
    parsed_url = urlparse(repo_url.rstrip("/"))
    if not parsed_url.path:
        raise ValueError("Invalid GitHub repository URL")

    # Extract repository name from the URL path
    # Handle both 'github.com/owner/repo' and 'github.com/owner/repo.git'
    path_parts = parsed_url.path.strip("/").split("/")
    if len(path_parts) != 2:
        raise ValueError("Invalid GitHub repository URL format")

    repo_name = path_parts[1].replace(".git", "")

    # Create the target directory if it doesn't exist
    folder_path = Path(folder_path).resolve()
    folder_path.mkdir(parents=True, exist_ok=True)

    # Generate the full path where the repository will be cloned
    repo_path = folder_path / repo_name

    # If repository already exists and has .git folder, return its path
    logger.info(f"Repository path: {repo_path}")
    if repo_path.exists() or (repo_path / ".git").exists():
        return str(repo_path)

    try:
        # Check if git is installed
        subprocess.run(["git", "--version"], check=True, capture_output=True)

        # Construct the git URL
        git_url = f"https://github.com/{path_parts[0]}/{path_parts[1]}.git"

        # Clone the repository
        subprocess.run(
            ["git", "clone", git_url, str(repo_path)],
            check=True,
            capture_output=True,
            text=True,
        )

        # Verify the repository was cloned successfully
        if not (repo_path / ".git").exists():
            raise subprocess.CalledProcessError(1, "git clone")

        return str(repo_path)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error cloning repository: {e}")
        if e.stderr:
            logger.error(f"Git error message: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def create_cache(display_name: str, documentation: str, system_prompt: str, gemini_api_key=None):
    # Configure Gemini API with the provided key or use the default
    configure_gemini_api(gemini_api_key)
    
    # Delete old caches with the same display name
    max_retries = 3
    retry_delay = 2 # seconds
    cache_list = None
    for attempt in range(max_retries):
        try:
            cache_list = caching.CachedContent.list()
            logger.info(f"Successfully listed caches on attempt {attempt + 1}")
            break # Success, exit loop
        except exceptions.ServiceUnavailable as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to list caches: {e}. Retrying in {retry_delay}s...")
            if attempt + 1 == max_retries:
                logger.error("Max retries reached for listing caches. Raising error.")
                raise # Re-raise the last exception if max retries reached
            time.sleep(retry_delay)
        except Exception as e: # Catch other potential exceptions during list
            logger.error(f"Unexpected error listing caches on attempt {attempt + 1}: {e}")
            raise # Re-raise unexpected errors immediately

    if cache_list is not None:
        logger.info(f"Result of caching.CachedContent.list(): {cache_list}")
        logger.info(f"Type of cache_list: {type(cache_list)}")
        for cache in cache_list:
            if cache is not None:
                if cache.display_name == display_name:
                    return cache.name
            else:
                logger.warning("Encountered None value while iterating through cache_list")
    cache = caching.CachedContent.create(
        model=CONTEXT_CACHING_RETRIVER,
        display_name=display_name,  # used to identify the cache
        contents=documentation,
        system_instruction=system_prompt,
        ttl=datetime.timedelta(minutes=30),
    )
    return cache.name


def delete_cache(display_name: str):
    # Delete old display name
    cache_list = caching.CachedContent.list()
    for cache in cache_list:
        if cache.display_name == display_name:
            cache.delete()
            return None


import os


def process_repo_link(link: str, gemini_api_key=None):
    display_name = link.split("/")[-1]
    documentation_path = f"docstrings_json/{display_name}.json"
    documentation_md_path = f"ducomentations_json/{display_name}.json"
    config_path = f"configs_json/{display_name}.json"
    repo_path = clone_github_repo("repository_folder", link)

    system_prompt = """
# Context
You are an expert Software developer with a deep understanding of the software development lifecycle, including requirements gathering, design, implementation, testing, and deployment.
Your task is to answer any question related to the documentation of the python repository repository_name that you have in your context.


""".replace(
        "repository_name", display_name
    )

    # Check if documentation file already exists
    if os.path.exists(documentation_path):
        # Load existing documentation
        with open(documentation_path, "r") as f:
            documentation_json = json.load(f)

        # Load existing config and documentation_md if they exist
        config = None # Initialize config
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f) # Load config as JSON
        documentation_md = None # Initialize documentation_md
        if os.path.exists(documentation_md_path):
            with open(documentation_md_path, "r") as f:
                documentation_md = json.load(f) # Load documentation_md as JSON
    else:
        
        # If file doesn't exist, proceed with repo cloning and documentation generation
        url_file_classification = "http://classifier:8002/score"

        # Get the documentation json from the fastapi documentation generation server
        logger.info(f"Calling classifier service for {repo_path}")
        api_key_preview = gemini_api_key[:5] if gemini_api_key and len(gemini_api_key) >= 5 else gemini_api_key
        logger.info(f"Using GEMINI_API_KEY: {api_key_preview}... (length: {len(gemini_api_key) if gemini_api_key else 0})")
        
        payload = {
            "repo_local_path": str(repo_path), 
            "GEMINI_API_KEY": gemini_api_key,
            "ANTHROPIC_API_KEY": "",
            "OPENAI_API_KEY": ""
        }
        
        response = requests.post(url_file_classification, json=payload) # Use repo_path directly
        if response.status_code != 200:
            raise Exception("Failed to get documentation from the server.")
        response = response.json()

        documentation_json = {"documentation": response["documentation"]}
        documentation_md_json = {"documentation_md": response["documentation_md"]}
        config_json = {"config": response["config"]}

        logger.info(f"Loaded existing documentation_json")
        logger.info(f"Loaded existing config")
        logger.info(f"Loaded existing documentation_md")

        # Save the documentation_json to a file
        with open(documentation_path, "w") as f1:
            json.dump(documentation_json, f1, indent=4)
        # Save the config_json to a file
        with open(documentation_md_path, "w") as f2:
            json.dump(documentation_md_json, f2, indent=4)
        # Save the config_json to a file
        with open(config_path, "w") as f3:
            json.dump(config_json, f3, indent=4)

    documentation_str = str(documentation_json)
    cache_name = create_cache(display_name, documentation_str, system_prompt, gemini_api_key)

    return cache_name


def process_local_folder(repo_path_str: str, gemini_api_key=None):
    """
    Process a local repository folder that has already been copied to the shared volume.

    Args:
        repo_path_str (str): The path to the repository folder within the shared volume.

    Returns:
        str: The name of the created or updated context cache.

    Raises:
        Exception: If processing fails (e.g., classifier service error).
    """
    repo_path = Path(repo_path_str)
    if not repo_path.is_dir():
        raise ValueError(f"Provided path is not a directory: {repo_path_str}")

    display_name = repo_path.name
    documentation_path = Path(f"docstrings_json/{display_name}.json")
    documentation_md_path = Path(f"ducomentations_json/{display_name}.json")
    config_path = Path(f"configs_json/{display_name}.json")

    # Ensure parent directories exist
    documentation_path.parent.mkdir(parents=True, exist_ok=True)
    documentation_md_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.parent.mkdir(parents=True, exist_ok=True)


    system_prompt = """
# Context
You are an expert Software developer with a deep understanding of the software development lifecycle, including requirements gathering, design, implementation, testing, and deployment.
Your task is to answer any question related to the documentation of the python repository repository_name that you have in your context.


""".replace("repository_name", display_name)

    # Check if documentation file already exists
    if documentation_path.exists():
        logger.info(f"Documentation already exists for {display_name}, loading...")
        # Load existing documentation
        with open(documentation_path, "r") as f:
            documentation_json = json.load(f)
        logger.info(f"Loaded existing documentation_json")

    else:
        logger.info(f"Documentation not found for {display_name}, generating...")
        # If file doesn't exist, proceed with documentation generation
        url_file_classification = "http://classifier:8002/score"

        # Get the documentation json from the fastapi documentation generation server
        logger.info(f"Calling classifier service for local folder: {repo_path}")
        api_key_preview = gemini_api_key[:5] if gemini_api_key and len(gemini_api_key) >= 5 else gemini_api_key
        logger.info(f"Using GEMINI_API_KEY: {api_key_preview}... (length: {len(gemini_api_key) if gemini_api_key else 0})")
        
        payload = {
            "repo_local_path": str(repo_path), 
            "GEMINI_API_KEY": gemini_api_key,
            "ANTHROPIC_API_KEY": "",
            "OPENAI_API_KEY": ""
        }
        
        try:
            response = requests.post(url_file_classification, json=payload)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to classifier service: {e}")
            raise Exception(f"Failed to connect to classifier service: {e}")
        except Exception as e:
            logger.error(f"Error during classifier request: {e}")
            raise Exception(f"Error during classifier request: {e}")

        if response.status_code != 200:
             logger.error(f"Classifier service returned status {response.status_code}: {response.text}")
             raise Exception(f"Classifier service failed with status {response.status_code}.")

        response_data = response.json()
        logger.info(f"Received response from classifier: {response_data}")


        documentation_json = {"documentation": response_data.get("documentation", {})}
        documentation_md_json = {"documentation_md": response_data.get("documentation_md", "")}
        config_json = {"config": response_data.get("config", {})}


        # Save the generated data
        try:
            with open(documentation_path, "w") as f1:
                json.dump(documentation_json, f1, indent=4)
            with open(documentation_md_path, "w") as f2:
                json.dump(documentation_md_json, f2, indent=4)
            with open(config_path, "w") as f3:
                json.dump(config_json, f3, indent=4)
            logger.info(f"Successfully saved generated documentation for {display_name}")
        except IOError as e:
            logger.error(f"Failed to write documentation files: {e}")
            raise Exception(f"Failed to write documentation files: {e}")


    documentation_str = str(documentation_json) # Use the structure containing 'documentation' key
    cache_name = create_cache(display_name, documentation_str, system_prompt, gemini_api_key)
    logger.info(f"Cache created/updated for {display_name}: {cache_name}")

    return cache_name


# def process_repo_link(link : str):
#     display_name = link.split('/')[-1]
#     repo_path = clone_github_repo("repository_folder",link)

#     system_prompt = """
# # Context
# You are an expert Software developer with a deep understanding of the software development lifecycle, including requirements gathering, design, implementation, testing, and deployment.
# Your task is to answer any question related to the documentation of the python repository repository_name that you have in your context.


# """.replace("repository_name",display_name)


#     url_file_classification = "http://localhost:8002/score"

#     #get the documentation json from the fastapi documentation generation server
#     response = requests.post(
#         url_file_classification,
#         json={
#             "repo_local_path": repo_path
#         }
#     )
#     if response.status_code != 200:
#         raise Exception("Failed to get documentation from the server.")

#     documentation_json = response.json()

#     with open(f'docstrings_json/{display_name}.json', 'w') as f:
#         json.dump(response.json(), f)

#     documentation_str = str(documentation_json)

#     cache_name = create_cache(display_name,documentation_str,system_prompt)

#     return cache_name

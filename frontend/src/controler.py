# controler.py
import os
import sys
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import shutil
import requests
import json
import logging
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

# Pydantic models (moved from model_server.py)
from pydantic import BaseModel, ConfigDict as PydanticConfigDict

# Add the parent directory to the path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir) # Add opendeepwiki root directory first

print(f"System path: {sys.path}")

try:
    print("Attempting to import from src.core.init_repo...")
    from src.core.init_repo import init_repo, handle_zip_upload
    print("Successfully imported backend functions from src.core.init_repo")
except Exception as general_e:
    print(f"An unexpected error occurred during import: {general_e}")
    print(traceback.format_exc())
    sys.exit(1)

# Attempt to import default chat model clients from src.core.chat_models
try:
    print("Attempting to import default chat model clients from src.core.chat_models...")
    from src.core.chat_models import (
        client_8b as default_client_8b,
        client_flash as default_client_flash,
        client_pro as default_client_pro,
        client_exp_pro as default_client_exp_pro,
        client_exp_flash as default_client_exp_flash,
    )
    print("Successfully imported default chat model clients.")
except ImportError as e:
    print(f"Warning: Could not import default chat model clients from src.core.chat_models: {e}")
    default_client_8b = None
    default_client_flash = None
    default_client_pro = None
    default_client_exp_pro = None
    default_client_exp_flash = None

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.INFO)
controller_logger = logging.getLogger(__name__)

# Thread pool executor (moved from model_server.py)
executor = ThreadPoolExecutor(max_workers=40)

# URL for Custom Documentalist (moved from model_server.py)
custom_doc_url = "http://localhost:8001/score"

# Multi-repository session management
repository_sessions = {}
session_lock = threading.Lock()

def get_session_id():
    """Generate a simple session ID. In production, use proper session management."""
    # For simplicity, using a single global session. In production, implement proper session management.
    return "global_session"

def get_repositories_for_session(session_id):
    """Get the list of repositories for a session."""
    with session_lock:
        return repository_sessions.get(session_id, {})

def add_repository_to_session(session_id, repo_name, cache_id):
    """Add a repository to the session."""
    with session_lock:
        if session_id not in repository_sessions:
            repository_sessions[session_id] = {}
        repository_sessions[session_id][repo_name] = {
            'cache_id': cache_id,
            'status': 'active',
            'added_at': json.dumps({}),  # You could add timestamp here
        }

def remove_repository_from_session(session_id, repo_name):
    """Remove a repository from the session."""
    with session_lock:
        if session_id in repository_sessions and repo_name in repository_sessions[session_id]:
            del repository_sessions[session_id][repo_name]
            return True
        return False

# Pydantic models for request and response (moved from model_server.py)
class GenerateRequestModel(BaseModel):
    message: str
    model_name: str
    cache_id: str
    repo_name: str
    target_repositories: list = None  # Optional list of repositories to query
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    model_config = PydanticConfigDict(protected_namespaces=())

# QueryResponse is not strictly needed for Flask but can be used for documentation/consistency
# class QueryResponse(BaseModel):
#     response: str

@app.route('/api/initialize', methods=['POST', 'OPTIONS'])
def initialize_repo():
    """Initialize the first repository or add to existing repositories"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        repo_link = data.get('repo_link', '')
        
        controller_logger.info(f"Received initialization request for repo: {repo_link}")
        
        if not repo_link:
            return jsonify({'error': 'Repository link is required'}), 400
        
        try:
            gemini_api_key = data.get('GEMINI_API_KEY', '')
            api_key_preview = gemini_api_key[:5] + "..." if gemini_api_key and len(gemini_api_key) > 5 else gemini_api_key
            controller_logger.info(f"Received GEMINI_API_KEY: {api_key_preview} (length: {len(gemini_api_key) if gemini_api_key else 0})")
            
            controller_logger.info(f"Calling init_repo with {repo_link}")
            repo_params, message = init_repo(repo_link, gemini_api_key) # from src.core.init_repo
            controller_logger.info(f"init_repo returned: {repo_params}, {message}")
            
            # Add to session
            session_id = get_session_id()
            if repo_params and repo_params.get('repo_name') and repo_params.get('cache_id'):
                add_repository_to_session(session_id, repo_params['repo_name'], repo_params['cache_id'])
            
            # Get all repositories for this session
            all_repositories = get_repositories_for_session(session_id)
            
            response = jsonify({
                'repo_params': repo_params,
                'message': message,
                'all_repositories': all_repositories
            })
            return response
            
        except Exception as e:
            controller_logger.error(f"Error in init_repo call: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        controller_logger.error(f"Error in initialize_repo endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_repo', methods=['POST', 'OPTIONS'])
def add_repository():
    """Add an additional repository to the current session"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        repo_link = data.get('repo_link', '')
        
        controller_logger.info(f"Received add repository request for repo: {repo_link}")
        
        if not repo_link:
            return jsonify({'error': 'Repository link is required'}), 400
        
        try:
            gemini_api_key = data.get('GEMINI_API_KEY', '')
            
            # Process the repository
            repo_params, message = init_repo(repo_link, gemini_api_key)
            controller_logger.info(f"init_repo returned: {repo_params}, {message}")
            
            # Add to session
            session_id = get_session_id()
            if repo_params and repo_params.get('repo_name') and repo_params.get('cache_id'):
                add_repository_to_session(session_id, repo_params['repo_name'], repo_params['cache_id'])
            
            # Get all repositories for this session
            all_repositories = get_repositories_for_session(session_id)
            
            response = jsonify({
                'repo_params': repo_params,
                'message': message,
                'all_repositories': all_repositories
            })
            return response
            
        except Exception as e:
            controller_logger.error(f"Error in add_repo call: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        controller_logger.error(f"Error in add_repository endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/list_repos', methods=['GET', 'OPTIONS'])
def list_repositories():
    """Get list of all repositories in the current session"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        session_id = get_session_id()
        all_repositories = get_repositories_for_session(session_id)
        
        return jsonify({
            'repositories': all_repositories
        })
            
    except Exception as e:
        controller_logger.error(f"Error in list_repositories endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/remove_repo', methods=['POST', 'OPTIONS'])
def remove_repository():
    """Remove a repository from the current session"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        repo_name = data.get('repo_name', '')
        
        if not repo_name:
            return jsonify({'error': 'Repository name is required'}), 400
        
        session_id = get_session_id()
        success = remove_repository_from_session(session_id, repo_name)
        
        if success:
            all_repositories = get_repositories_for_session(session_id)
            return jsonify({
                'message': f'Successfully removed repository: {repo_name}',
                'all_repositories': all_repositories
            })
        else:
            return jsonify({'error': f'Repository {repo_name} not found in session'}), 404
            
    except Exception as e:
        controller_logger.error(f"Error in remove_repository endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_repo():
    """Upload a repository as a zip file using the existing handle_zip_upload function"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not file.filename.endswith('.zip'):
            return jsonify({'error': 'File must be a zip archive'}), 400
        
        try:
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, secure_filename(file.filename))
            file.save(temp_path)
            
            controller_logger.info(f"Saved uploaded file to {temp_path}")
            
            gemini_api_key = request.form.get('GEMINI_API_KEY', '')
            api_key_preview = gemini_api_key[:5] + "..." if gemini_api_key and len(gemini_api_key) > 5 else gemini_api_key
            controller_logger.info(f"Received GEMINI_API_KEY for upload: {api_key_preview} (length: {len(gemini_api_key) if gemini_api_key else 0})")
            
            generator = handle_zip_upload(temp_path, gemini_api_key) # from src.core.init_repo
            
            repo_params = {"repo_name": "", "cache_id": ""}
            message = "Processing..."
            
            for result in generator:
                repo_params, message = result
                controller_logger.info(f"handle_zip_upload yielded: {repo_params}, {message}")
            
            # Add to session
            session_id = get_session_id()
            if repo_params and repo_params.get('repo_name') and repo_params.get('cache_id'):
                add_repository_to_session(session_id, repo_params['repo_name'], repo_params['cache_id'])
            
            # Get all repositories for this session
            all_repositories = get_repositories_for_session(session_id)
            
            shutil.rmtree(temp_dir)
            
            return jsonify({
                'repo_params': repo_params,
                'message': message,
                'all_repositories': all_repositories
            })
        except Exception as e:
            controller_logger.error(f"Error in handle_zip_upload call: {str(e)}", exc_info=True)
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        controller_logger.error(f"Error in upload_repo endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST', 'OPTIONS'])
def generate_response():
    """
    Generate a response from the AI. Enhanced for multi-repository support.
    """
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    try:
        data = request.get_json()
        try:
            req_data = GenerateRequestModel(**data)
        except Exception as pydantic_exc:
            controller_logger.error(f"Request validation error: {pydantic_exc}")
            return jsonify({'error': f"Invalid request payload: {pydantic_exc}"}), 400

        controller_logger.info(f"Received generate request for model: {req_data.model_name} with message: '{req_data.message[:100]}...'")

        # Get repositories for multi-repo processing
        session_id = get_session_id()
        all_repositories = get_repositories_for_session(session_id)
        
        # Determine target repositories
        target_repos = []
        if req_data.target_repositories:
            # Use specified repositories
            target_repos = [repo for repo in req_data.target_repositories if repo in all_repositories]
        elif req_data.repo_name and req_data.repo_name in all_repositories:
            # Fallback to single repository for backward compatibility
            target_repos = [req_data.repo_name]
        elif all_repositories:
            # Use all available repositories
            target_repos = list(all_repositories.keys())
        
        if not target_repos:
            return jsonify({'error': 'No repositories available for query. Please initialize at least one repository.'}), 400

        controller_logger.info(f"Querying repositories: {target_repos}")

        # --- API Client Initialization (adapted from model_server.py) ---
        # Gemini clients
        client_8b_instance = default_client_8b
        client_exp_flash_instance = default_client_exp_flash
        client_exp_pro_instance = default_client_exp_pro
        client_flash_instance = default_client_flash
        client_pro_instance = default_client_pro

        if req_data.GEMINI_API_KEY:
            controller_logger.info("GEMINI_API_KEY provided in request, configuring new Gemini clients.")
            import google.generativeai as genai
            try:
                # This configure call is global to the genai module.
                # Potential concurrency issues if not handled carefully by SDK or with locks.
                # Replicating model_server.py behavior which also did this.
                genai.configure(api_key=req_data.GEMINI_API_KEY)
                
                safe_settings = [
                    {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
                common_config = {"temperature": 0, "top_p": 1, "max_output_tokens": 8000}
                
                client_8b_instance = genai.GenerativeModel("gemini-1.5-flash-8b-001", safety_settings=safe_settings, generation_config=common_config)
                client_exp_flash_instance = genai.GenerativeModel("gemini-2.0-flash-exp", safety_settings=safe_settings, generation_config=common_config)
                client_exp_pro_instance = genai.GenerativeModel("gemini-exp-1206", safety_settings=safe_settings, generation_config=common_config)
                client_flash_instance = genai.GenerativeModel("gemini-1.5-flash-002", safety_settings=safe_settings, generation_config=common_config)
                client_pro_instance = genai.GenerativeModel("gemini-1.5-pro-002", safety_settings=safe_settings, generation_config=common_config)
            except Exception as e:
                controller_logger.error(f"Error initializing Gemini client with provided key: {e}", exc_info=True)
                # Fallback to default clients or handle error; current logic uses defaults if this fails.
        elif not all([default_client_8b, default_client_flash, default_client_pro, default_client_exp_pro, default_client_exp_flash]):
             controller_logger.warning("Default Gemini clients are not available and no API key provided in request.")
             # This might lead to errors if a Gemini model is chosen without a configured client.

        # OpenAI client
        openai_client = None
        openai_api_key_to_use = req_data.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if openai_api_key_to_use:
            from openai import OpenAI as OpenAIClient # Alias
            try:
                openai_client = OpenAIClient(api_key=openai_api_key_to_use)
            except Exception as e:
                controller_logger.error(f"Error initializing OpenAI client: {e}", exc_info=True)
        else:
            if req_data.model_name == "o3": # This model name uses OpenAI
                 controller_logger.warning("OpenAI API key not configured, but required for 'o3'.")


        response_text = ""

        if "gemini" in req_data.model_name:
            target_client = None
            if req_data.model_name == "gemini-exp-1206": target_client = client_exp_pro_instance
            elif req_data.model_name == "gemini-2.0-flash-exp": target_client = client_exp_flash_instance
            elif req_data.model_name == "gemini-1.5-flash-8b-001": target_client = client_8b_instance
            elif req_data.model_name == "gemini-1.5-flash-002": target_client = client_flash_instance
            elif req_data.model_name == "gemini-1.5-pro-002": target_client = client_pro_instance
            
            if not target_client:
                raise ValueError(f"Unknown Gemini model or client not initialized: {req_data.model_name}")

            future = executor.submit(target_client.generate_content, [req_data.message])
            gemini_response = future.result() 
            response_text = gemini_response.text

        elif req_data.model_name == "o3": # This actually uses OpenAI "o3"
            if not openai_client:
                raise ValueError("OpenAI client not initialized. Cannot use model 'o3' (which maps to OpenAI 'o3').")
            
            def get_openai_o3_response(prompt_text):
                api_response = openai_client.chat.completions.create( # Standard OpenAI SDK call
                        model="o3", # Using a standard model name, "o3" is likely an alias or custom.
                        messages=[{"role": "user", "content": prompt_text}],
                        reasoning={"effort": "high"}, # This is not a standard OpenAI parameter
                    )
                return api_response.choices[0].message.content

            future = executor.submit(get_openai_o3_response, req_data.message)
            response_text = future.result()

        elif req_data.model_name == "Custom Documentalist":
            # Multi-repository Custom Documentalist processing
            if len(target_repos) == 1:
                # Single repository - use existing logic
                repo_name = target_repos[0]
                cache_id = all_repositories[repo_name]['cache_id']
                
                payload = {
                    "repository_name": repo_name,
                    "cache_id": cache_id,
                    "user_problem": req_data.message,
                    "GEMINI_API_KEY": req_data.GEMINI_API_KEY,
                    "ANTHROPIC_API_KEY": req_data.ANTHROPIC_API_KEY,
                    "OPENAI_API_KEY": req_data.OPENAI_API_KEY,
                }
                try:
                    # Paths are assumed to be in a Docker context /app directory
                    with open(f"/app/docstrings_json/{repo_name}.json", "r") as f:
                        payload["documentation"] = json.load(f)
                    # Typo "ducomentations_json" matches original model_server.py
                    with open(f"/app/ducomentations_json/{repo_name}.json", "r") as f:
                        payload["documentation_md"] = json.load(f)
                    with open(f"/app/configs_json/{repo_name}.json", "r") as f:
                        payload["config"] = json.load(f)
                except FileNotFoundError as fnf_error:
                    controller_logger.error(f"JSON file not found for Custom Documentalist: {fnf_error}")
                    raise Exception(f"Required JSON file not found for {repo_name}: {fnf_error.filename}") from fnf_error
                
                def post_to_custom_documentalist():
                    return requests.post(custom_doc_url, json=payload, timeout=180) # Increased timeout

                future = executor.submit(post_to_custom_documentalist)
                external_response = future.result()
                external_response.raise_for_status() 
                response_text = external_response.json()["libraire_response"]
            else:
                # Multi-repository processing - call repo_chat service with multiple repositories
                payload = {
                    "user_problem": req_data.message,
                    "target_repositories": target_repos,
                    "repository_data": {},
                    "GEMINI_API_KEY": req_data.GEMINI_API_KEY,
                    "ANTHROPIC_API_KEY": req_data.ANTHROPIC_API_KEY,
                    "OPENAI_API_KEY": req_data.OPENAI_API_KEY,
                }
                
                # Load data for each target repository
                for repo_name in target_repos:
                    cache_id = all_repositories[repo_name]['cache_id']
                    try:
                        with open(f"/app/docstrings_json/{repo_name}.json", "r") as f:
                            documentation = json.load(f)
                        with open(f"/app/ducomentations_json/{repo_name}.json", "r") as f:
                            documentation_md = json.load(f)
                        with open(f"/app/configs_json/{repo_name}.json", "r") as f:
                            config = json.load(f)
                        
                        payload["repository_data"][repo_name] = {
                            "cache_id": cache_id,
                            "documentation": documentation,
                            "documentation_md": documentation_md,
                            "config": config
                        }
                    except FileNotFoundError as fnf_error:
                        controller_logger.warning(f"JSON file not found for repository {repo_name}: {fnf_error}")
                        # Continue with other repositories
                        continue

                # Call the multi-repo endpoint
                multi_repo_url = "http://localhost:8001/multi_repo_score"
                
                def post_to_multi_repo_documentalist():
                    return requests.post(multi_repo_url, json=payload, timeout=300) # Longer timeout for multi-repo

                try:
                    future = executor.submit(post_to_multi_repo_documentalist)
                    external_response = future.result()
                    external_response.raise_for_status()
                    response_data = external_response.json()
                    response_text = response_data["libraire_response"]
                except requests.exceptions.ConnectionError:
                    # Fallback: if multi-repo endpoint doesn't exist, process sequentially
                    controller_logger.info("Multi-repo endpoint not available, falling back to sequential processing")
                    responses = []
                    for repo_name in target_repos:
                        if repo_name in payload["repository_data"]:
                            repo_data = payload["repository_data"][repo_name]
                            single_payload = {
                                "repository_name": repo_name,
                                "cache_id": repo_data["cache_id"],
                                "user_problem": f"[Repository: {repo_name}] {req_data.message}",
                                "documentation": repo_data["documentation"],
                                "documentation_md": repo_data["documentation_md"],
                                "config": repo_data["config"],
                                "GEMINI_API_KEY": req_data.GEMINI_API_KEY,
                                "ANTHROPIC_API_KEY": req_data.ANTHROPIC_API_KEY,
                                "OPENAI_API_KEY": req_data.OPENAI_API_KEY,
                            }
                            try:
                                single_response = requests.post(custom_doc_url, json=single_payload, timeout=180)
                                single_response.raise_for_status()
                                repo_response = single_response.json()["libraire_response"]
                                responses.append(f"## Response from {repo_name}:\n{repo_response}")
                            except Exception as e:
                                controller_logger.error(f"Error querying repository {repo_name}: {e}")
                                responses.append(f"## Repository {repo_name}:\nError: {str(e)}")
                    
                    response_text = "\n\n".join(responses)
        
        else:
            return jsonify({'error': f"Unknown model_name: {req_data.model_name}"}), 400

        return jsonify({'response': response_text})

    except ValueError as ve:
        controller_logger.error(f"Value error processing generate request: {ve}", exc_info=True)
        return jsonify({'error': str(ve)}), 400
    except requests.exceptions.RequestException as http_err:
        controller_logger.error(f"HTTP error during Custom Documentalist call: {http_err}", exc_info=True)
        return jsonify({'error': f"Error calling external service: {http_err}"}), 502
    except Exception as e:
        controller_logger.error(f"Error generating response: {e}", exc_info=True)
        return jsonify({'error': f"Internal server error: {str(e)}"}), 500


def _build_cors_preflight_response():
    response = jsonify({})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

if __name__ == '__main__':
    port = 5050 # controler.py's original port
    controller_logger.info(f"Starting Flask server on port {port}")
    # Enable threading for Flask dev server to better utilize ThreadPoolExecutor
    app.run(host='0.0.0.0', port=port, threaded=True)
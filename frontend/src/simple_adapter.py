"""
Adapter script to connect the React frontend with the existing Python backend.
This script creates a Flask server that directly calls the existing functions.
"""

import os
import sys
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import shutil

# Add the parent directory to the path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir) # Add opendeepwiki root directory first

print(f"System path: {sys.path}")

# Import the actual backend functions
try:
    print("Attempting to import from src.front_init_repo...")
    from src.front_init_repo import init_repo, handle_zip_upload, respond
    print("Successfully imported backend functions from src.front_init_repo")
except ImportError as e:
    print(f"Error importing from src.front_init_repo: {e}")
    print("Attempting to import from front_init_repo...")
    try:
        from front_init_repo import init_repo, handle_zip_upload, respond
        print("Successfully imported backend functions from front_init_repo")
    except ImportError as final_e:
        print(f"Error importing from front_init_repo: {final_e}")
        print("Failed to import backend functions. Exiting.")
        sys.exit(1)
except Exception as general_e:
    print(f"An unexpected error occurred during import: {general_e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/initialize', methods=['POST', 'OPTIONS'])
def initialize_repo():
    """Initialize a repository from a URL by directly calling the existing init_repo function"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        repo_link = data.get('repo_link', '')
        
        print(f"Received initialization request for repo: {repo_link}")
        
        if not repo_link:
            return jsonify({'error': 'Repository link is required'}), 400
        
        try:
            # Get API keys from the request if provided
            gemini_api_key = data.get('GEMINI_API_KEY', '')
            
            # Log API key info (safely)
            api_key_preview = gemini_api_key[:5] if gemini_api_key and len(gemini_api_key) >= 5 else gemini_api_key
            print(f"Received GEMINI_API_KEY: {api_key_preview}... (length: {len(gemini_api_key) if gemini_api_key else 0})")
            
            # Directly call the existing init_repo function
            print(f"Calling init_repo with {repo_link}")
            repo_params, message = init_repo(repo_link, gemini_api_key)
            print(f"init_repo returned: {repo_params}, {message}")
            
            response = jsonify({
                'repo_params': repo_params,
                'message': message
            })
            return response
            
        except Exception as e:
            import traceback
            print(f"Error in init_repo: {str(e)}, GEMINI_API_KEY: {gemini_api_key}")
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        import traceback
        print(f"Error in initialize_repo: {str(e)}, GEMINI_API_KEY: {gemini_api_key}")
        print(traceback.format_exc())
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
            # Save the uploaded file to a temporary location
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, secure_filename(file.filename))
            file.save(temp_path)
            
            print(f"Saved uploaded file to {temp_path}")
            
            # Get API keys from the form data if provided
            gemini_api_key = request.form.get('GEMINI_API_KEY', '')
            
            # Log API key info (safely)
            api_key_preview = gemini_api_key[:5] if gemini_api_key and len(gemini_api_key) >= 5 else gemini_api_key
            print(f"Received GEMINI_API_KEY for upload: {api_key_preview}... (length: {len(gemini_api_key) if gemini_api_key else 0})")
            
            # Use the generator function directly
            generator = handle_zip_upload(temp_path, gemini_api_key)
            
            # Get the final result (last yielded value)
            repo_params = {"repo_name": "", "cache_id": ""}
            message = "Processing..."
            
            for result in generator:
                repo_params, message = result
                print(f"handle_zip_upload yielded: {repo_params}, {message}")
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            return jsonify({
                'repo_params': repo_params,
                'message': message
            })
        except Exception as e:
            import traceback
            print(f"Error in handle_zip_upload: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        import traceback
        print(f"Error in upload_repo: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST', 'OPTIONS'])
def generate_response():
    """Generate a response from the AI using the existing respond function"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        model_name = data.get('model_name', '')
        repo_params = {
            'repo_name': data.get('repo_name', ''),
            'cache_id': data.get('cache_id', ''),
            'GEMINI_API_KEY': data.get('GEMINI_API_KEY', ''),
            'ANTHROPIC_API_KEY': data.get('ANTHROPIC_API_KEY', ''),
            'OPENAI_API_KEY': data.get('OPENAI_API_KEY', '')
        }
        
        print(f"Received generate request with message: {message}")
        
        # Parse history from the message format used in the original code
        history = []
        if message:
            lines = message.split('\n')
            i = 0
            while i < len(lines):
                if i + 1 < len(lines) and lines[i].startswith('User: ') and lines[i+1].startswith('Expert: '):
                    user_msg = lines[i][6:]  # Remove 'User: ' prefix
                    expert_msg = lines[i+1][8:]  # Remove 'Expert: ' prefix
                    history.append((user_msg, expert_msg))
                    i += 2
                else:
                    i += 1
        
        print(f"Parsed history: {history}")
        
        try:
            # Extract the actual user message (the last part after "User: ")
            actual_message = message.split('User: ')[-1].strip()
            print(f"Actual message to respond to: {actual_message}")
            
            # Directly call the existing respond function
            response_text = respond(actual_message, history, model_name, repo_params)
            print(f"Response: {response_text}")
            return jsonify({'response': response_text})
        except Exception as e:
            import traceback
            print(f"Error in respond: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        import traceback
        print(f"Error in generate_response: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def _build_cors_preflight_response():
    response = jsonify({})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

if __name__ == '__main__':
    port = 5050
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
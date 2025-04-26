"""
Mock adapter script to connect the React frontend with the backend.
This script creates a minimal Flask server that responds to API requests with mock data.
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import shutil

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Mock functions
def mock_init_repo(repo_link):
    """Mock function to initialize a repository"""
    print(f"Mock init_repo called with {repo_link}")
    repo_name = repo_link.split('/')[-1].replace('.git', '')
    return {
        "repo_name": repo_name,
        "cache_id": "mock_cache_id"
    }, f"Successfully initialized repository: {repo_name}"

def mock_handle_zip_upload(uploaded_zip_file):
    """Mock function to handle zip upload"""
    print(f"Mock handle_zip_upload called with {uploaded_zip_file}")
    repo_name = os.path.basename(uploaded_zip_file).replace('.zip', '')
    yield {
        "repo_name": repo_name,
        "cache_id": "mock_cache_id"
    }, f"Successfully uploaded repository: {repo_name}"

def mock_respond(message, history, model_name, repo_params):
    """Mock function to respond to a message"""
    print(f"Mock respond called with {message}, {model_name}, {repo_params}")
    return f"This is a mock response to: {message}"

@app.route('/api/initialize', methods=['POST', 'OPTIONS'])
def initialize_repo():
    """Initialize a repository from a URL"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        repo_link = data.get('repo_link', '')
        
        print(f"Received initialization request for repo: {repo_link}")
        
        if not repo_link:
            return jsonify({'error': 'Repository link is required'}), 400
        
        repo_params, message = mock_init_repo(repo_link)
        
        response = jsonify({
            'repo_params': repo_params,
            'message': message
        })
        return response
        
    except Exception as e:
        import traceback
        print(f"Error in initialize_repo: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_repo():
    """Upload a repository as a zip file"""
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
            
            # Use the generator function directly
            generator = mock_handle_zip_upload(temp_path)
            
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
    """Generate a response from the AI"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        model_name = data.get('model_name', '')
        repo_params = {
            'repo_name': data.get('repo_name', ''),
            'cache_id': data.get('cache_id', '')
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
            
            # Call the mock respond function
            response_text = mock_respond(actual_message, history, model_name, repo_params)
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
    app.run(host='0.0.0.0', port=port, debug=True)
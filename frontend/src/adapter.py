"""
Adapter script to connect the React frontend with the existing Python backend.
This script creates a simple Flask server that directly calls the existing functions.
"""

import os
import sys
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from werkzeug.utils import secure_filename
import tempfile
import shutil

# Add the parent directory to the path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
sys.path.append(os.path.dirname(parent_dir))  # Add opendeepwiki root directory
sys.path.append('/workspace/opendeepwiki')  # Add absolute path to opendeepwiki root directory

# Mock the functions for testing
def init_repo(repo_link):
    print(f"Mock init_repo called with {repo_link}")
    return {
        "repo_name": repo_link.split('/')[-1].replace('.git', ''),
        "cache_id": "mock_cache_id"
    }, f"Successfully initialized repository: {repo_link.split('/')[-1].replace('.git', '')}"

def handle_zip_upload(uploaded_zip_file):
    print(f"Mock handle_zip_upload called with {uploaded_zip_file}")
    repo_name = "uploaded_repo"
    yield {
        "repo_name": repo_name,
        "cache_id": "mock_cache_id"
    }, f"Successfully uploaded repository: {repo_name}"

def respond(message, history, model_name, repo_param):
    print(f"Mock respond called with {message}, {model_name}, {repo_param}")
    return f"This is a mock response to: {message}"

app = Flask(__name__)
# Configure CORS to allow requests from any origin
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"], 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

@app.route('/api/initialize', methods=['POST'])
def initialize_repo():
    """Initialize a repository from a URL by directly calling the existing init_repo function"""
    try:
        data = request.json
        if not data:
            print("No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400
            
        repo_link = data.get('repo_link', '')
        print(f"Received initialization request for repo: {repo_link}")
        
        if not repo_link:
            print("Repository link is required")
            return jsonify({'error': 'Repository link is required'}), 400
        
        try:
            # Directly call the existing init_repo function
            print(f"Calling init_repo with {repo_link}")
            repo_params, message = init_repo(repo_link)
            print(f"init_repo returned: {repo_params}, {message}")
            
            response = jsonify({
                'repo_params': repo_params,
                'message': message
            })
            print(f"Sending response: {response}")
            return response
            
        except Exception as e:
            import traceback
            print(f"Error in init_repo: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        import traceback
        print(f"Error in initialize_repo: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_repo():
    """Upload a repository as a zip file using the existing handle_zip_upload function"""
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
        
        # Use the generator function directly
        generator = handle_zip_upload(temp_path)
        
        # Get the final result (last yielded value)
        repo_params = {"repo_name": "", "cache_id": ""}
        message = "Processing..."
        
        for result in generator:
            repo_params, message = result
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return jsonify({
            'repo_params': repo_params,
            'message': message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_response():
    """Generate a response from the AI using the existing respond function"""
    print("Received generate request")
    data = request.json
    print(f"Request data: {data}")
    
    message = data.get('message', '')
    model_name = data.get('model_name', '')
    repo_params = {
        'repo_name': data.get('repo_name', ''),
        'cache_id': data.get('cache_id', '')
    }
    
    print(f"Message: {message}")
    print(f"Model: {model_name}")
    print(f"Repo params: {repo_params}")
    
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
        print(f"Error in generate_response: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Add a health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5015, debug=True)
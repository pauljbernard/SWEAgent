import axios from 'axios';

const API_URL = 'http://localhost:5050/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});

/**
 * Initialize a repository from a URL
 * @param {string} repoUrl - The URL of the repository to initialize
 * @param {Object} apiKeys - The API keys for different models
 * @returns {Promise<Object>} - The repository parameters and status message
 */
export const initializeRepository = async (repoUrl, apiKeys = {}) => {
  try {
    console.log('Initializing repository:', repoUrl);
    const payload = {
      repo_link: repoUrl,
      GEMINI_API_KEY: apiKeys.GEMINI_API_KEY || '',
      ANTHROPIC_API_KEY: apiKeys.ANTHROPIC_API_KEY || '',
      OPENAI_API_KEY: apiKeys.OPENAI_API_KEY || ''
    };
    
    console.log('Sending initialization request with API keys:', {
      ...payload,
      GEMINI_API_KEY: payload.GEMINI_API_KEY ? '***' : '',
      ANTHROPIC_API_KEY: payload.ANTHROPIC_API_KEY ? '***' : '',
      OPENAI_API_KEY: payload.OPENAI_API_KEY ? '***' : ''
    });
    
    const response = await apiClient.post('/initialize', payload);
    console.log('Repository initialized successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error initializing repository:', error);
    console.error('Error details:', error.response ? error.response.data : 'No response data');
    throw error;
  }
};

/**
 * Upload a local repository as a zip file
 * @param {File} zipFile - The zip file containing the repository
 * @param {Object} apiKeys - The API keys for different models
 * @returns {Promise<Object>} - The repository parameters and status message
 */
export const uploadRepository = async (zipFile, apiKeys = {}) => {
  try {
    const formData = new FormData();
    formData.append('file', zipFile);
    
    // Add API keys to the form data
    formData.append('GEMINI_API_KEY', apiKeys.GEMINI_API_KEY || '');
    formData.append('ANTHROPIC_API_KEY', apiKeys.ANTHROPIC_API_KEY || '');
    formData.append('OPENAI_API_KEY', apiKeys.OPENAI_API_KEY || '');
    
    console.log('Uploading repository with API keys');
    
    const response = await apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    console.error('Error uploading repository:', error);
    throw error;
  }
};

/**
 * Send a message to the AI and get a response
 * @param {string} message - The user's message
 * @param {Array} history - The conversation history
 * @param {string} modelName - The name of the model to use
 * @param {Object} repoParams - The repository parameters
 * @param {Object} apiKeys - The API keys for different models
 * @returns {Promise<string>} - The AI's response
 */
export const sendMessage = async (message, history, modelName, repoParams, apiKeys = {}) => {
  try {
    // Convert history to the format expected by the backend
    // The backend expects a string with the format "User: message\nExpert: response\n"
    let historyText = '';
    
    // Process all messages in the history
    for (let i = 0; i < history.length; i++) {
      if (history[i].role === 'user') {
        historyText += `User: ${history[i].content}\n`;
      } else if (history[i].role === 'assistant') {
        historyText += `Expert: ${history[i].content}\n`;
      }
      // Skip system messages
    }
    
    // Add the current message
    historyText += `User: ${message}\n`;
    
    const payload = {
      message: historyText,
      model_name: modelName,
      cache_id: repoParams.cache_id || '',
      repo_name: repoParams.repo_name || '',
      // Include API keys in the payload
      GEMINI_API_KEY: apiKeys.GEMINI_API_KEY || '',
      ANTHROPIC_API_KEY: apiKeys.ANTHROPIC_API_KEY || '',
      OPENAI_API_KEY: apiKeys.OPENAI_API_KEY || ''
    };
    
    console.log('Sending message with payload:', {
      ...payload,
      GEMINI_API_KEY: payload.GEMINI_API_KEY ? '***' : '',
      ANTHROPIC_API_KEY: payload.ANTHROPIC_API_KEY ? '***' : '',
      OPENAI_API_KEY: payload.OPENAI_API_KEY ? '***' : ''
    });
    
    const response = await apiClient.post('/generate', payload);
    console.log('Message response received:', response.data);
    return response.data.response;
  } catch (error) {
    console.error('Error sending message:', error);
    console.error('Error details:', error.response ? error.response.data : 'No response data');
    throw error;
  }
};

export default {
  initializeRepository,
  uploadRepository,
  sendMessage,
};
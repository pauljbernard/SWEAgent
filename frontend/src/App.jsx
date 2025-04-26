import React, { useState, useEffect } from 'react';
import { FiPlus, FiMenu, FiX, FiGithub, FiUpload, FiUser, FiMessageSquare, FiTrash2, FiSettings } from 'react-icons/fi';
import api from './services/api';
import ChatMessages from './components/chat/ChatMessages';
import ChatInput from './components/chat/ChatInput';
import ConfigModal from './components/sidebar/ConfigModal';

// Simple function to generate a unique ID (fallback if uuid package fails)
const generateUniqueId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
};

// Helper functions for localStorage
const saveToLocalStorage = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Error saving to localStorage:', error);
  }
};

const loadFromLocalStorage = (key, defaultValue) => {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : defaultValue;
  } catch (error) {
    console.error('Error loading from localStorage:', error);
    return defaultValue;
  }
};

// Helper function to generate a random conversation name
const generateConversationName = (messages) => {
  if (messages.length === 0) return "New conversation";
  
  // Use the first user message as the conversation name
  const firstUserMessage = messages.find(msg => msg.role === 'user');
  if (firstUserMessage) {
    // Truncate the message if it's too long
    const truncated = firstUserMessage.content.substring(0, 30);
    return truncated + (firstUserMessage.content.length > 30 ? '...' : '');
  }
  
  return "New conversation";
};

const App = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [repoParams, setRepoParams] = useState(loadFromLocalStorage('repoParams', { repo_name: '', cache_id: '' }));
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState(loadFromLocalStorage('selectedModel', 'gemini-1.5-flash-8b-001'));
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [repoUrl, setRepoUrl] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');
  
  // API keys state
  const [apiKeys, setApiKeys] = useState({
    GEMINI_API_KEY: localStorage.getItem('GEMINI_API_KEY') || '',
    ANTHROPIC_API_KEY: localStorage.getItem('ANTHROPIC_API_KEY') || '',
    OPENAI_API_KEY: localStorage.getItem('OPENAI_API_KEY') || ''
  });
  
  // State for the config modal
  const [configModalOpen, setConfigModalOpen] = useState(false);
  
  // State for managing multiple conversations
  const [conversations, setConversations] = useState(loadFromLocalStorage('conversations', {}));
  const [activeConversationId, setActiveConversationId] = useState(null);
  
  // Initialize or load active conversation when repo is initialized
  useEffect(() => {
    if (repoParams.repo_name) {
      // Check if we have conversations for this repo
      const repoConversations = conversations[repoParams.repo_name] || [];
      
      if (repoConversations.length > 0) {
        // If there are existing conversations, set the active one to the most recent
        const mostRecentConversation = repoConversations[0];
        setActiveConversationId(mostRecentConversation.id);
        setChatHistory(mostRecentConversation.messages);
        
        // Add a system message to indicate that conversation was loaded
        const systemMessage = {
          role: 'system',
          content: `Loaded conversation: ${mostRecentConversation.name}`
        };
        setChatHistory(prev => [...prev, systemMessage]);
        setTimeout(() => {
          setChatHistory(prev => prev.filter(msg => msg !== systemMessage));
        }, 3000);
      } else {
        // If no conversations exist for this repo, create a new one
        const newConversationId = generateUniqueId();
        setActiveConversationId(newConversationId);
        setChatHistory([]);
        
        // Initialize the conversations object for this repo
        setConversations(prev => ({
          ...prev,
          [repoParams.repo_name]: [
            {
              id: newConversationId,
              name: "New conversation",
              messages: [],
              createdAt: new Date().toISOString()
            }
          ]
        }));
      }
    }
  }, [repoParams.repo_name]);
  
  // Save active conversation when chat history changes
  useEffect(() => {
    if (repoParams.repo_name && activeConversationId && chatHistory.length > 0) {
      // Filter out system messages before saving
      const historyToSave = chatHistory.filter(msg => msg.role !== 'system');
      
      if (historyToSave.length > 0) {
        // Update the conversation in the conversations state
        setConversations(prev => {
          const repoConversations = prev[repoParams.repo_name] || [];
          const conversationIndex = repoConversations.findIndex(conv => conv.id === activeConversationId);
          
          if (conversationIndex !== -1) {
            // Update existing conversation
            const updatedConversations = [...repoConversations];
            updatedConversations[conversationIndex] = {
              ...updatedConversations[conversationIndex],
              messages: historyToSave,
              name: generateConversationName(historyToSave),
              updatedAt: new Date().toISOString()
            };
            
            return {
              ...prev,
              [repoParams.repo_name]: updatedConversations
            };
          }
          
          return prev;
        });
      }
    }
  }, [chatHistory, repoParams.repo_name, activeConversationId]);
  
  // Save conversations to localStorage when they change
  useEffect(() => {
    saveToLocalStorage('conversations', conversations);
  }, [conversations]);
  
  // Save repo params to localStorage when they change
  useEffect(() => {
    if (repoParams.repo_name) {
      saveToLocalStorage('repoParams', repoParams);
    }
  }, [repoParams]);
  
  // Save selected model to localStorage when it changes
  useEffect(() => {
    saveToLocalStorage('selectedModel', selectedModel);
  }, [selectedModel]);
  
  // Apply dark mode class to body
  useEffect(() => {
    document.body.classList.add('dark');
    
    return () => {
      document.body.classList.remove('dark');
    };
  }, []);
  
  const handleSendMessage = async (message) => {
    if (!message.trim() || !repoParams.repo_name) return;
    
    try {
      setIsLoading(true);
      
      // Add user message to history
      const userMessage = { role: 'user', content: message };
      const updatedHistory = [...chatHistory, userMessage];
      setChatHistory(updatedHistory);
      
      // Filter out system messages before sending to API
      const historyForApi = updatedHistory.filter(msg => msg.role !== 'system');
      
      console.log('Sending message with history:', historyForApi);
      
      // Call API to get response with API keys
      const response = await api.sendMessage(
        message, 
        historyForApi, 
        selectedModel, 
        repoParams,
        apiKeys // Pass the API keys to the API service
      );
      
      // Add assistant response to history
      const assistantMessage = { role: 'assistant', content: response };
      setChatHistory([...updatedHistory, assistantMessage]);
      
      console.log('Updated chat history:', [...updatedHistory, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setChatHistory([
        ...chatHistory,
        { role: 'user', content: message },
        { role: 'assistant', content: `Error: ${error.message || 'Failed to get response from server.'}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleInitRepo = async () => {
    if (!repoUrl.trim()) return;
    
    try {
      setIsLoading(true);
      setStatusMessage('Initializing repository...\nThis may take some time,\nif first time (not more then 10 minutes)...');
      
      const result = await api.initializeRepository(repoUrl, apiKeys);
      
      // Check if we're switching to a different repository
      if (repoParams.repo_name !== result.repo_params.repo_name) {
        // Load chat history for the new repository if it exists
        const historyKey = `chatHistory_${result.repo_params.repo_name}`;
        const savedHistory = loadFromLocalStorage(historyKey, []);
        setChatHistory(savedHistory);
      }
      
      setRepoParams(result.repo_params);
      setStatusMessage(result.message);
    } catch (error) {
      console.error('Error initializing repository:', error);
      setStatusMessage(`Error: ${error.message || 'Failed to initialize repository'}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.zip')) {
      setUploadStatus('Error: Please upload a .zip file');
      return;
    }
    
    try {
      setIsLoading(true);
      setUploadStatus(`Uploading ${file.name}\nThis may take some time,\nif first time (not more then 10 minutes)...`);
      
      const result = await api.uploadRepository(file, apiKeys);
      
      // Check if we're switching to a different repository
      if (repoParams.repo_name !== result.repo_params.repo_name) {
        // Load chat history for the new repository if it exists
        const historyKey = `chatHistory_${result.repo_params.repo_name}`;
        const savedHistory = loadFromLocalStorage(historyKey, []);
        setChatHistory(savedHistory);
      }
      
      setRepoParams(result.repo_params);
      setUploadStatus(result.message);
    } catch (error) {
      console.error('Error uploading file:', error);
      setUploadStatus(`Error: ${error.message || 'Failed to upload file'}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };
  
  const handleApiKeysUpdate = (newApiKeys) => {
    setApiKeys(newApiKeys);
    // The keys are already saved to localStorage in the ConfigModal component
  };
  
  const handleNewChat = () => {
    if (!repoParams.repo_name) return;
    
    // Create a new conversation
    const newConversationId = generateUniqueId();
    
    // Add the new conversation to the conversations state
    setConversations(prev => {
      const repoConversations = prev[repoParams.repo_name] || [];
      
      return {
        ...prev,
        [repoParams.repo_name]: [
          {
            id: newConversationId,
            name: "New conversation",
            messages: [],
            createdAt: new Date().toISOString()
          },
          ...repoConversations // Add existing conversations after the new one
        ]
      };
    });
    
    // Set the new conversation as active
    setActiveConversationId(newConversationId);
    
    // Clear the chat history
    setChatHistory([]);
  };
  
  const handleSelectConversation = (conversationId) => {
    if (!repoParams.repo_name) return;
    
    // Find the selected conversation
    const repoConversations = conversations[repoParams.repo_name] || [];
    const selectedConversation = repoConversations.find(conv => conv.id === conversationId);
    
    if (selectedConversation) {
      // Set the selected conversation as active
      setActiveConversationId(conversationId);
      
      // Load the conversation history
      setChatHistory(selectedConversation.messages);
      
      // Add a system message to indicate that conversation was loaded
      const systemMessage = {
        role: 'system',
        content: `Loaded conversation: ${selectedConversation.name}`
      };
      setChatHistory(prev => [...prev, systemMessage]);
      setTimeout(() => {
        setChatHistory(prev => prev.filter(msg => msg !== systemMessage));
      }, 3000);
    }
  };
  
  const handleDeleteConversation = (conversationId, e) => {
    e.stopPropagation(); // Prevent triggering the parent click event
    
    if (!repoParams.repo_name) return;
    
    // Remove the conversation from the conversations state
    setConversations(prev => {
      const repoConversations = prev[repoParams.repo_name] || [];
      const updatedConversations = repoConversations.filter(conv => conv.id !== conversationId);
      
      return {
        ...prev,
        [repoParams.repo_name]: updatedConversations
      };
    });
    
    // If the deleted conversation was active, set the first conversation as active
    if (conversationId === activeConversationId) {
      const repoConversations = conversations[repoParams.repo_name] || [];
      const remainingConversations = repoConversations.filter(conv => conv.id !== conversationId);
      
      if (remainingConversations.length > 0) {
        setActiveConversationId(remainingConversations[0].id);
        setChatHistory(remainingConversations[0].messages);
      } else {
        // If no conversations remain, create a new one
        handleNewChat();
      }
    }
  };
  
  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar" style={{transform: sidebarVisible ? 'translateX(0)' : 'translateX(-100%)', position: 'fixed'}}>
        <div className="sidebar-header">
          <button className="new-chat-button" onClick={handleNewChat} disabled={!repoParams.repo_name}>
            <FiPlus size={16} /> New chat
          </button>
          <button className="sidebar-close-button" onClick={toggleSidebar}>
            <FiX />
          </button>
        </div>
        
        <div className="sidebar-content">
          {/* API Configuration */}
          <h3 className="sidebar-section-title">API CONFIGURATION</h3>
          <button 
            className="action-button"
            onClick={() => setConfigModalOpen(true)}
          >
            <FiSettings size={16} />
            Configure API Keys
          </button>
          
          {/* Conversations list */}
          {repoParams.repo_name && (
            <>
              <h3 className="sidebar-section-title">CONVERSATIONS</h3>
              <div className="conversations-list">
                {conversations[repoParams.repo_name]?.map(conversation => (
                  <div 
                    key={conversation.id} 
                    className={`conversation-item ${activeConversationId === conversation.id ? 'active' : ''}`}
                    onClick={() => handleSelectConversation(conversation.id)}
                  >
                    <FiMessageSquare size={16} />
                    <span className="conversation-name">{conversation.name}</span>
                    <button 
                      className="conversation-delete-button"
                      onClick={(e) => handleDeleteConversation(conversation.id, e)}
                      aria-label="Delete conversation"
                    >
                      <FiTrash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
              
              <div className="separator"></div>
            </>
          )}
          
          <h3 className="sidebar-section-title">MODEL</h3>
          <select 
            className="model-selector"
            value={selectedModel} 
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            <option value="gemini-1.5-flash-8b-001">gemini-1.5-flash-8b-001</option>
            <option value="gemini-1.5-flash-002">gemini-1.5-flash-002</option>
            <option value="gemini-1.5-pro-002">gemini-1.5-pro-002</option>
            <option value="gemini-exp-1206">gemini-exp-1206</option>
            <option value="gemini-2.0-flash-exp">gemini-2.0-flash-exp</option>
            <option value="Claude-3.7-Sonnet-32k-budget">Claude-3.7-Sonnet-32k-budget</option>
            <option value="Custom Documentalist">Custom Documentalist</option>
          </select>
          
          <h3 className="sidebar-section-title">REPOSITORY</h3>
          <input 
            className="repo-input"
            placeholder="Enter repository link" 
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
          />
          <button 
            className="action-button primary"
            onClick={handleInitRepo} 
            disabled={isLoading || !repoUrl.trim()}
          >
            <FiGithub size={16} />
            {isLoading ? 'Initializing...' : 'Initialize Repository'}
          </button>
          
          <div className="separator"></div>
          
          <h3 className="sidebar-section-title">LOCAL REPOSITORY</h3>
          <label className="file-upload-label">
            <FiUpload size={16} />
            Upload Repository (.zip)
            <input 
              type="file" 
              accept=".zip" 
              onChange={handleFileUpload}
              disabled={isLoading}
              style={{display: 'none'}}
            />
          </label>
          
          {uploadStatus && (
            <div className="status-message">{uploadStatus}</div>
          )}
          
          {statusMessage && (
            <div className="status-message">{statusMessage}</div>
          )}
        </div>
        
        <div className="sidebar-footer">
          opendeepwiki v1.0.0 - AI-Powered Code Documentation Assistant
        </div>
      </div>
      
      {/* Main Content */}
      <div className="main-content" style={{marginLeft: sidebarVisible ? '260px' : '0', width: sidebarVisible ? 'calc(100% - 260px)' : '100%', transition: 'margin-left 0.3s ease, width 0.3s ease'}}>
        <div className="header">
          {!sidebarVisible && (
            <button className="header-button" onClick={toggleSidebar}>
              <FiMenu />
            </button>
          )}
          <div className="header-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: '0.5rem', display: 'inline-block', verticalAlign: 'middle' }}>
              <rect width="24" height="24" rx="4" fill="#10a37f" />
              <path d="M8 12L11 15L16 9" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span style={{verticalAlign: 'middle'}}>{repoParams.repo_name ? `opendeepwiki - ${repoParams.repo_name}` : 'opendeepwiki'}</span>
          </div>
          <button className="header-button">
            Share
          </button>
        </div>
        
        <div className="chat-container">
          {chatHistory.length > 0 ? (
            <ChatMessages messages={chatHistory} />
          ) : (
            <div className="empty-state">
              <h1 className="empty-state-title">What can I help with?</h1>
              <p className="empty-state-subtitle">
                {repoParams.repo_name 
                  ? `Ask me anything about the ${repoParams.repo_name} repository. I can help you understand the code, documentation, and more.` 
                  : 'Initialize a repository from the sidebar to get started. You can use a GitHub URL or upload a local repository.'}
              </p>
            </div>
          )}
        </div>
        
        <ChatInput 
          onSendMessage={handleSendMessage} 
          disabled={!repoParams.repo_name || isLoading}
          isLoading={isLoading}
          placeholder={repoParams.repo_name ? "Message opendeepwiki..." : "Initialize a repository to start chatting..."}
        />
      </div>
      
      {/* Configuration Modal */}
      <ConfigModal 
        isOpen={configModalOpen} 
        onClose={() => setConfigModalOpen(false)} 
        onSave={handleApiKeysUpdate} 
      />
    </div>
  );
};

export default App;
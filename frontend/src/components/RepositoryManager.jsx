import React, { useState, useEffect } from 'react';
import { FiPlus, FiTrash2, FiGithub, FiUpload, FiFolder, FiCheck, FiX } from 'react-icons/fi';
import api from '../services/api';

const RepositoryManager = ({ 
  repositories, 
  setRepositories, 
  apiKeys, 
  onStatusMessage,
  activeRepositories,
  setActiveRepositories 
}) => {
  const [isAddingRepo, setIsAddingRepo] = useState(false);
  const [newRepoUrl, setNewRepoUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Load repositories on component mount
  useEffect(() => {
    const loadRepositories = async () => {
      try {
        const response = await api.listRepositories();
        if (response.repositories) {
          setRepositories(response.repositories);
          // Set all repositories as active by default
          setActiveRepositories(Object.keys(response.repositories));
        }
      } catch (error) {
        console.error('Error loading repositories:', error);
      }
    };

    loadRepositories();
  }, [setRepositories, setActiveRepositories]);

  const handleAddRepository = async () => {
    if (!newRepoUrl.trim()) {
      onStatusMessage('Please enter a repository URL');
      return;
    }

    setIsLoading(true);
    onStatusMessage('Adding repository...');

    try {
      const response = await api.addRepository(newRepoUrl, apiKeys);
      if (response.all_repositories) {
        setRepositories(response.all_repositories);
        // Add the new repository to active repositories
        if (response.repo_params && response.repo_params.repo_name) {
          setActiveRepositories(prev => [...new Set([...prev, response.repo_params.repo_name])]);
        }
      }
      onStatusMessage(response.message || 'Repository added successfully');
      setNewRepoUrl('');
      setIsAddingRepo(false);
    } catch (error) {
      console.error('Error adding repository:', error);
      onStatusMessage(`Error adding repository: ${error.response?.data?.error || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveRepository = async (repoName) => {
    if (!window.confirm(`Are you sure you want to remove repository "${repoName}"?`)) {
      return;
    }

    try {
      const response = await api.removeRepository(repoName);
      if (response.all_repositories) {
        setRepositories(response.all_repositories);
        // Remove from active repositories
        setActiveRepositories(prev => prev.filter(name => name !== repoName));
      }
      onStatusMessage(response.message || 'Repository removed successfully');
    } catch (error) {
      console.error('Error removing repository:', error);
      onStatusMessage(`Error removing repository: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleToggleRepository = (repoName) => {
    setActiveRepositories(prev => {
      if (prev.includes(repoName)) {
        return prev.filter(name => name !== repoName);
      } else {
        return [...prev, repoName];
      }
    });
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.zip')) {
      onStatusMessage('Please select a ZIP file');
      return;
    }

    setIsLoading(true);
    onStatusMessage('Uploading repository...');

    try {
      const response = await api.uploadRepository(file, apiKeys);
      if (response.all_repositories) {
        setRepositories(response.all_repositories);
        // Add the new repository to active repositories
        if (response.repo_params && response.repo_params.repo_name) {
          setActiveRepositories(prev => [...new Set([...prev, response.repo_params.repo_name])]);
        }
      }
      onStatusMessage(response.message || 'Repository uploaded successfully');
    } catch (error) {
      console.error('Error uploading repository:', error);
      onStatusMessage(`Error uploading repository: ${error.response?.data?.error || error.message}`);
    } finally {
      setIsLoading(false);
      // Reset the file input
      event.target.value = '';
    }
  };

  return (
    <div className="repository-manager">
      <div className="section-header">
        <h3 className="text-lg font-semibold text-gray-200 mb-4 flex items-center">
          <FiFolder className="mr-2" />
          Repositories ({Object.keys(repositories).length})
        </h3>
      </div>

      {/* Repository List */}
      <div className="repository-list mb-4">
        {Object.entries(repositories).map(([repoName, repoData]) => (
          <div key={repoName} className="repository-item mb-2 p-3 bg-gray-700 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <button
                  onClick={() => handleToggleRepository(repoName)}
                  className={`mr-3 p-1 rounded ${
                    activeRepositories.includes(repoName)
                      ? 'text-green-400 hover:text-green-300'
                      : 'text-gray-500 hover:text-gray-400'
                  }`}
                  title={activeRepositories.includes(repoName) ? 'Repository active' : 'Repository inactive'}
                >
                  {activeRepositories.includes(repoName) ? <FiCheck /> : <FiX />}
                </button>
                <div>
                  <div className="text-sm font-medium text-gray-200">{repoName}</div>
                  <div className="text-xs text-gray-400">
                    Status: {repoData.status || 'active'}
                  </div>
                </div>
              </div>
              <button
                onClick={() => handleRemoveRepository(repoName)}
                className="text-red-400 hover:text-red-300 p-1"
                title="Remove repository"
              >
                <FiTrash2 />
              </button>
            </div>
          </div>
        ))}

        {Object.keys(repositories).length === 0 && (
          <div className="text-gray-500 text-sm text-center py-4">
            No repositories loaded
          </div>
        )}
      </div>

      {/* Active Repositories Summary */}
      {activeRepositories.length > 0 && (
        <div className="active-repos-summary mb-4 p-2 bg-blue-900/50 rounded-lg">
          <div className="text-xs text-blue-300 mb-1">Active for queries:</div>
          <div className="text-sm text-blue-200">
            {activeRepositories.join(', ')}
          </div>
        </div>
      )}

      {/* Add Repository Section */}
      {!isAddingRepo ? (
        <div className="add-repository-buttons space-y-2">
          <button
            onClick={() => setIsAddingRepo(true)}
            disabled={isLoading}
            className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <FiPlus className="mr-2" />
            Add Repository
          </button>
          
          {/* File Upload Button */}
          <label className="w-full px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center cursor-pointer">
            <FiUpload className="mr-2" />
            Upload ZIP
            <input
              type="file"
              accept=".zip"
              onChange={handleFileUpload}
              disabled={isLoading}
              className="hidden"
            />
          </label>
        </div>
      ) : (
        <div className="add-repository-form space-y-2">
          <div className="flex">
            <input
              type="text"
              value={newRepoUrl}
              onChange={(e) => setNewRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="flex-1 px-3 py-2 bg-gray-700 text-white rounded-l-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              onClick={handleAddRepository}
              disabled={isLoading || !newRepoUrl.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <FiGithub className="mr-1" />
              Add
            </button>
          </div>
          <button
            onClick={() => {
              setIsAddingRepo(false);
              setNewRepoUrl('');
            }}
            disabled={isLoading}
            className="w-full px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        </div>
      )}

      {isLoading && (
        <div className="loading-indicator mt-4 text-center">
          <div className="text-sm text-gray-400">Processing...</div>
        </div>
      )}
    </div>
  );
};

export default RepositoryManager; 
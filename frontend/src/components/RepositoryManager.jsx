import React, { useState, useEffect } from 'react';
import { FiPlus, FiTrash2, FiGithub, FiUpload, FiFolder, FiCheck, FiX, FiLoader, FiExternalLink, FiDownload, FiGitBranch, FiArchive } from 'react-icons/fi';
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
  const [loadingRepo, setLoadingRepo] = useState(null);
  const [statusType, setStatusType] = useState('info'); // 'info', 'success', 'error', 'loading'

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

  const showStatus = (message, type = 'info') => {
    setStatusType(type);
    onStatusMessage(message);
    
    // Auto-clear success messages after 3 seconds
    if (type === 'success') {
      setTimeout(() => {
        onStatusMessage('');
      }, 3000);
    }
  };

  const handleAddRepository = async () => {
    if (!newRepoUrl.trim()) {
      showStatus('❌ Please enter a repository URL', 'error');
      return;
    }

    setIsLoading(true);
    setLoadingRepo('url');
    showStatus('🔄 Initializing repository...', 'loading');

    try {
      const response = await api.addRepository(newRepoUrl, apiKeys);
      if (response.all_repositories) {
        setRepositories(response.all_repositories);
        // Add the new repository to active repositories
        if (response.repo_params && response.repo_params.repo_name) {
          setActiveRepositories(prev => [...new Set([...prev, response.repo_params.repo_name])]);
        }
      }
      showStatus(`✅ Successfully added ${response.repo_params?.repo_name || 'repository'}!`, 'success');
      setNewRepoUrl('');
      setIsAddingRepo(false);
    } catch (error) {
      console.error('Error adding repository:', error);
      showStatus(`❌ Failed to add repository: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      setIsLoading(false);
      setLoadingRepo(null);
    }
  };

  const handleRemoveRepository = async (repoName) => {
    if (!window.confirm(`Are you sure you want to remove "${repoName}"?\n\nThis action cannot be undone.`)) {
      return;
    }

    setLoadingRepo(repoName);
    showStatus(`🗑️ Removing ${repoName}...`, 'loading');

    try {
      const response = await api.removeRepository(repoName);
      if (response.all_repositories) {
        setRepositories(response.all_repositories);
        // Remove from active repositories
        setActiveRepositories(prev => prev.filter(name => name !== repoName));
      }
      showStatus(`✅ Successfully removed ${repoName}!`, 'success');
    } catch (error) {
      console.error('Error removing repository:', error);
      showStatus(`❌ Failed to remove repository: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      setLoadingRepo(null);
    }
  };

  const handleToggleRepository = (repoName) => {
    setActiveRepositories(prev => {
      const newActive = prev.includes(repoName) 
        ? prev.filter(name => name !== repoName)
        : [...prev, repoName];
      
      const action = prev.includes(repoName) ? 'deactivated' : 'activated';
      showStatus(`📁 Repository ${repoName} ${action}`, 'info');
      
      return newActive;
    });
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.zip')) {
      showStatus('❌ Please select a ZIP file', 'error');
      return;
    }

    setIsLoading(true);
    setLoadingRepo('upload');
    showStatus(`📦 Uploading ${file.name}...`, 'loading');

    try {
      const response = await api.uploadRepository(file, apiKeys);
      if (response.all_repositories) {
        setRepositories(response.all_repositories);
        // Add the new repository to active repositories
        if (response.repo_params && response.repo_params.repo_name) {
          setActiveRepositories(prev => [...new Set([...prev, response.repo_params.repo_name])]);
        }
      }
      showStatus(`✅ Successfully uploaded ${response.repo_params?.repo_name || 'repository'}!`, 'success');
    } catch (error) {
      console.error('Error uploading repository:', error);
      showStatus(`❌ Upload failed: ${error.response?.data?.error || error.message}`, 'error');
    } finally {
      setIsLoading(false);
      setLoadingRepo(null);
      // Reset the file input
      event.target.value = '';
    }
  };

  return (
    <div className="repository-manager">
      {/* Modern Header */}
      <div className="repo-header">
        <div className="repo-header-content">
          <div className="repo-title-section">
            <div className="repo-icon">
              <FiFolder size={20} />
            </div>
            <h3 className="repo-title">Repositories</h3>
          </div>
          <div className="repo-count-badge">
            {Object.keys(repositories).length}
          </div>
        </div>
      </div>

      {/* Repository List */}
      <div className="repository-list">
        {Object.entries(repositories).map(([repoName, repoData]) => (
          <div key={repoName} className="repo-card">
            <div className="repo-card-content">
              <div className="repo-toggle">
                <button
                  onClick={() => handleToggleRepository(repoName)}
                  className={`toggle-btn ${activeRepositories.includes(repoName) ? 'active' : 'inactive'}`}
                  title={activeRepositories.includes(repoName) ? 'Click to deactivate' : 'Click to activate'}
                >
                  <div className="toggle-indicator">
                    {activeRepositories.includes(repoName) ? <FiCheck size={14} /> : <FiX size={14} />}
                  </div>
                </button>
              </div>
              
              <div className="repo-info">
                <div className="repo-name-row">
                  <span className="repo-name">{repoName}</span>
                  {activeRepositories.includes(repoName) && (
                    <span className="active-badge">Active</span>
                  )}
                </div>
                <div className="repo-status">
                  <div className="status-indicator"></div>
                  <span>Ready</span>
                </div>
              </div>
              
              <button
                onClick={() => handleRemoveRepository(repoName)}
                disabled={loadingRepo === repoName}
                className="remove-btn"
                title="Remove repository"
              >
                {loadingRepo === repoName ? (
                  <FiLoader className="spin" size={16} />
                ) : (
                  <FiTrash2 size={16} />
                )}
              </button>
            </div>
          </div>
        ))}

        {Object.keys(repositories).length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">
              <FiFolder size={48} />
            </div>
            <h4 className="empty-title">No repositories loaded</h4>
            <p className="empty-subtitle">
              Add your first repository to get started with multi-repo analysis
            </p>
          </div>
        )}
      </div>

      {/* Active Repositories Summary */}
      {activeRepositories.length > 0 && (
        <div className="active-summary">
          <div className="summary-header">
            <div className="pulse-indicator"></div>
            <span className="summary-title">Active for queries</span>
          </div>
          <div className="active-tags">
            {activeRepositories.map((repo) => (
              <span key={repo} className="repo-tag">
                {repo}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Modern Add Repository Section */}
      {!isAddingRepo ? (
        <div className="add-section">
          <button
            onClick={() => setIsAddingRepo(true)}
            disabled={isLoading}
            className="modern-btn primary-btn"
          >
            <div className="btn-content">
              <FiGitBranch size={18} />
              <span>Add Repository</span>
            </div>
            <div className="btn-glow"></div>
          </button>
          
          <label className="modern-btn upload-btn">
            <input
              type="file"
              accept=".zip"
              onChange={handleFileUpload}
              disabled={isLoading}
              style={{ display: 'none' }}
            />
            <div className="btn-content">
              {loadingRepo === 'upload' ? (
                <>
                  <FiLoader className="spin" size={18} />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <FiArchive size={18} />
                  <span>Upload ZIP</span>
                </>
              )}
            </div>
            <div className="btn-glow"></div>
          </label>
        </div>
      ) : (
        <div className="add-form">
          <div className="input-group">
            <div className="input-wrapper">
              <FiGithub className="input-icon" size={20} />
              <input
                type="text"
                value={newRepoUrl}
                onChange={(e) => setNewRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                className="modern-input"
                disabled={isLoading}
                onKeyPress={(e) => e.key === 'Enter' && handleAddRepository()}
              />
            </div>
          </div>
          
          <div className="form-actions">
            <button
              onClick={handleAddRepository}
              disabled={isLoading || !newRepoUrl.trim()}
              className="modern-btn action-btn"
            >
              <div className="btn-content">
                {loadingRepo === 'url' ? (
                  <>
                    <FiLoader className="spin" size={16} />
                    <span>Adding...</span>
                  </>
                ) : (
                  <>
                    <FiDownload size={16} />
                    <span>Add</span>
                  </>
                )}
              </div>
            </button>
            
            <button
              onClick={() => {
                setIsAddingRepo(false);
                setNewRepoUrl('');
              }}
              disabled={isLoading}
              className="modern-btn cancel-btn"
            >
              <span>Cancel</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RepositoryManager; 
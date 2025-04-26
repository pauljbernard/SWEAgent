import React, { useState } from 'react';
import styled from 'styled-components';
import { FiX, FiPlus, FiGithub, FiUpload, FiMessageSquare, FiSettings } from 'react-icons/fi';
import ConfigModal from './ConfigModal';

const SidebarContainer = styled.div`
  width: var(--sidebar-width);
  height: 100vh;
  background-color: ${props => props.theme === 'dark' ? 'var(--sidebar-bg-dark)' : '#f7f7f8'};
  border-right: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  overflow-y: auto;
  transition: transform 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  position: absolute;
  left: 0;
  top: 0;
  transform: ${props => props.visible ? 'translateX(0)' : 'translateX(-100%)'};
`;

const SidebarHeader = styled.div`
  padding: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
`;

const NewChatButton = styled.button`
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  background-color: transparent;
  color: ${props => props.theme === 'dark' ? 'var(--text-light)' : 'var(--text-dark)'};
  border: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  cursor: pointer;
  transition: background-color 0.2s ease;
  font-size: var(--font-size-sm);
  width: 100%;
  
  &:hover {
    background-color: ${props => props.theme === 'dark' ? 'var(--sidebar-hover-dark)' : 'rgba(0, 0, 0, 0.05)'};
  }
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.5)'};
  font-size: 1.2rem;
  padding: 0.3rem;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  
  &:hover {
    opacity: 1;
    background: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'};
  }
`;

const SidebarContent = styled.div`
  padding: var(--spacing-md);
  flex: 1;
  display: flex;
  flex-direction: column;
`;

const SectionTitle = styled.h2`
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.5)'};
  margin-bottom: var(--spacing-sm);
  margin-top: var(--spacing-lg);
  font-weight: 500;
  
  &:first-of-type {
    margin-top: 0;
  }
`;

const ModelSelector = styled.select`
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  border: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  background-color: ${props => props.theme === 'dark' ? 'rgba(0, 0, 0, 0.2)' : 'var(--background-light)'};
  color: ${props => props.theme === 'dark' ? 'var(--text-light)' : 'var(--text-dark)'};
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-sm);
`;

const RepoInput = styled.input`
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  border: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  background-color: ${props => props.theme === 'dark' ? 'rgba(0, 0, 0, 0.2)' : 'var(--background-light)'};
  color: ${props => props.theme === 'dark' ? 'var(--text-light)' : 'var(--text-dark)'};
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-sm);
`;

const ActionButton = styled.button`
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  background-color: ${props => props.primary ? 'var(--primary-color)' : 'transparent'};
  color: ${props => props.primary ? 'white' : props.theme === 'dark' ? 'var(--text-light)' : 'var(--text-dark)'};
  border: ${props => props.primary ? 'none' : `1px solid ${props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'}`};
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
  margin-bottom: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  
  &:hover {
    background-color: ${props => props.primary ? '#0d8c6d' : props.theme === 'dark' ? 'var(--sidebar-hover-dark)' : 'rgba(0, 0, 0, 0.05)'};
    transform: ${props => props.primary ? 'translateY(-1px)' : 'none'};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const Separator = styled.hr`
  border: none;
  border-top: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  margin: var(--spacing-md) 0;
`;

const StatusMessage = styled.div`
  padding: var(--spacing-sm);
  border-radius: var(--border-radius);
  background-color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'};
  color: ${props => props.theme === 'dark' ? 'var(--text-light)' : 'var(--text-dark)'};
  font-size: var(--font-size-xs);
  margin-top: var(--spacing-md);
`;

const FileUploadLabel = styled.label`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  background-color: transparent;
  color: ${props => props.theme === 'dark' ? 'var(--text-light)' : 'var(--text-dark)'};
  border: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  text-align: center;
  cursor: pointer;
  transition: background-color 0.2s ease;
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-sm);
  
  &:hover {
    background-color: ${props => props.theme === 'dark' ? 'var(--sidebar-hover-dark)' : 'rgba(0, 0, 0, 0.05)'};
  }
`;

const HiddenFileInput = styled.input`
  display: none;
`;

const SidebarFooter = styled.div`
  padding: var(--spacing-md);
  border-top: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  font-size: var(--font-size-xs);
  color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.5)'};
  text-align: center;
`;

const LeftSidebar = ({ 
  visible, 
  toggleSidebar, 
  selectedModel, 
  setSelectedModel, 
  onInitRepo,
  onInitializeRepo,
  onUploadRepo,
  statusMessage,
  isLoading: externalIsLoading,
  onApiKeysUpdate
}) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [configModalOpen, setConfigModalOpen] = useState(false);
  
  // Combine local and external loading states
  const isProcessing = isLoading || externalIsLoading;
  
  const isDarkMode = document.body.classList.contains('dark');
  const theme = isDarkMode ? 'dark' : 'light';
  
  const handleInitRepo = async () => {
    if (!repoUrl.trim()) return;
    
    setIsLoading(true);
    try {
      const result = await onInitializeRepo(repoUrl);
      if (result.success) {
        setUploadStatus('');
      }
    } catch (error) {
      console.error('Error initializing repository:', error);
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
    
    setUploadStatus(`Uploading ${file.name}...`);
    setIsLoading(true);
    
    try {
      const result = await onUploadRepo(file);
      if (result.success) {
        setUploadStatus(`Uploaded ${file.name}`);
      } else {
        setUploadStatus(`Error: ${result.message}`);
      }
    } catch (error) {
      setUploadStatus(`Error: ${error.message || 'Failed to upload file'}`);
      console.error('Error uploading file:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleApiKeysUpdate = (apiKeys) => {
    // Call the onApiKeysUpdate callback with the API keys
    if (onApiKeysUpdate) {
      onApiKeysUpdate(apiKeys);
    }
  };
  
  return (
    <SidebarContainer visible={visible} theme={theme}>
      <SidebarHeader theme={theme}>
        <NewChatButton theme={theme}>
          <FiPlus size={16} /> New chat
        </NewChatButton>
        <CloseButton onClick={toggleSidebar} theme={theme}>
          <FiX />
        </CloseButton>
      </SidebarHeader>
      
      <SidebarContent>
        <SectionTitle theme={theme}>API CONFIGURATION</SectionTitle>
        <ActionButton 
          onClick={() => setConfigModalOpen(true)}
          theme={theme}
        >
          <FiSettings size={16} />
          Configure API Keys
        </ActionButton>
        
        <SectionTitle theme={theme}>MODEL</SectionTitle>
        <ModelSelector 
          value={selectedModel} 
          onChange={(e) => setSelectedModel(e.target.value)}
          theme={theme}
        >
          <option value="gemini-1.5-flash-8b-001">gemini-1.5-flash-8b-001</option>
          <option value="gemini-1.5-flash-002">gemini-1.5-flash-002</option>
          <option value="gemini-1.5-pro-002">gemini-1.5-pro-002</option>
          <option value="gemini-exp-1206">gemini-exp-1206</option>
          <option value="gemini-2.0-flash-exp">gemini-2.0-flash-exp</option>
          <option value="Claude-3.7-Sonnet-32k-budget">Claude-3.7-Sonnet-32k-budget</option>
          <option value="Custom Documentalist">Custom Documentalist</option>
        </ModelSelector>
        
        <SectionTitle theme={theme}>REPOSITORY</SectionTitle>
        <RepoInput 
          type="text" 
          placeholder="Enter repository link" 
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          theme={theme}
        />
        <ActionButton 
          onClick={handleInitRepo} 
          disabled={isProcessing || !repoUrl.trim()}
          primary
          theme={theme}
        >
          <FiGithub size={16} />
          {isProcessing ? 'Initializing...' : 'Initialize Repository'}
        </ActionButton>
        
        <Separator theme={theme} />
        
        <SectionTitle theme={theme}>LOCAL REPOSITORY</SectionTitle>
        <FileUploadLabel theme={theme}>
          <FiUpload size={16} />
          Upload Repository (.zip)
          <HiddenFileInput 
            type="file" 
            accept=".zip" 
            onChange={handleFileUpload}
            disabled={isProcessing}
          />
        </FileUploadLabel>
        
        {uploadStatus && (
          <StatusMessage theme={theme}>
            {uploadStatus}
          </StatusMessage>
        )}
        
        {statusMessage && (
          <StatusMessage theme={theme}>
            {statusMessage}
          </StatusMessage>
        )}
      </SidebarContent>
      
      <SidebarFooter theme={theme}>
        opendeepwiki v1.0.0 - AI-Powered Code Documentation Assistant
      </SidebarFooter>
      
      {/* Configuration Modal */}
      <ConfigModal 
        isOpen={configModalOpen} 
        onClose={() => setConfigModalOpen(false)} 
        onSave={handleApiKeysUpdate} 
      />
    </SidebarContainer>
  );
};

export default LeftSidebar;
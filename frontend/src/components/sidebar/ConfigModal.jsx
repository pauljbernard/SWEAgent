import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiX, FiSettings } from 'react-icons/fi';

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
`;

const ModalContainer = styled.div`
  background-color: ${props => props.theme === 'dark' ? 'var(--sidebar-bg-dark)' : '#f7f7f8'};
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
`;

const ModalHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
`;

const ModalTitle = styled.h2`
  font-size: 1.2rem;
  color: ${props => props.theme === 'dark' ? 'var(--text-light)' : 'var(--text-dark)'};
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
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

const FormGroup = styled.div`
  margin-bottom: var(--spacing-md);
`;

const Label = styled.label`
  display: block;
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)'};
`;

const Input = styled.input`
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  border: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  background-color: ${props => props.theme === 'dark' ? 'rgba(0, 0, 0, 0.2)' : 'var(--background-light)'};
  color: ${props => props.theme === 'dark' ? 'var(--text-light)' : 'var(--text-dark)'};
  font-size: var(--font-size-sm);
  
  &:focus {
    outline: none;
    border-color: var(--primary-color);
  }
`;

const RequiredIndicator = styled.span`
  color: #ff4d4f;
  margin-left: var(--spacing-xs);
`;

const SaveButton = styled.button`
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  background-color: var(--primary-color);
  color: white;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
  font-size: var(--font-size-sm);
  
  &:hover {
    background-color: #0d8c6d;
    transform: translateY(-1px);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const HelpText = styled.p`
  font-size: var(--font-size-xs);
  color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.5)'};
  margin-top: var(--spacing-xs);
`;

const ConfigModal = ({ isOpen, onClose, onSave }) => {
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [anthropicApiKey, setAnthropicApiKey] = useState('');
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  
  const isDarkMode = document.body.classList.contains('dark');
  const theme = isDarkMode ? 'dark' : 'light';
  
  useEffect(() => {
    // Load saved API keys from localStorage when modal opens
    if (isOpen) {
      const savedGeminiKey = localStorage.getItem('GEMINI_API_KEY') || '';
      const savedAnthropicKey = localStorage.getItem('ANTHROPIC_API_KEY') || '';
      const savedOpenaiKey = localStorage.getItem('OPENAI_API_KEY') || '';
      
      setGeminiApiKey(savedGeminiKey);
      setAnthropicApiKey(savedAnthropicKey);
      setOpenaiApiKey(savedOpenaiKey);
    }
  }, [isOpen]);
  
  const handleSave = () => {
    // Save API keys to localStorage
    localStorage.setItem('GEMINI_API_KEY', geminiApiKey);
    localStorage.setItem('ANTHROPIC_API_KEY', anthropicApiKey);
    localStorage.setItem('OPENAI_API_KEY', openaiApiKey);
    
    // Call the onSave callback with the API keys
    onSave({
      GEMINI_API_KEY: geminiApiKey,
      ANTHROPIC_API_KEY: anthropicApiKey,
      OPENAI_API_KEY: openaiApiKey
    });
    
    onClose();
  };
  
  if (!isOpen) return null;
  
  return (
    <ModalOverlay onClick={onClose}>
      <ModalContainer theme={theme} onClick={e => e.stopPropagation()}>
        <ModalHeader>
          <ModalTitle theme={theme}>
            <FiSettings size={20} />
            API Configuration
          </ModalTitle>
          <CloseButton onClick={onClose} theme={theme}>
            <FiX />
          </CloseButton>
        </ModalHeader>
        
        <FormGroup>
          <Label theme={theme}>
            Gemini API Key <RequiredIndicator>*</RequiredIndicator>
          </Label>
          <Input
            type="password"
            value={geminiApiKey}
            onChange={e => setGeminiApiKey(e.target.value)}
            placeholder="Enter Gemini API Key"
            theme={theme}
            required
          />
          <HelpText theme={theme}>Required for Gemini models (gemini-*). Get your key at <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer">Google AI Studio</a></HelpText>
        </FormGroup>
        
        <FormGroup>
          <Label theme={theme}>
            Anthropic API Key
          </Label>
          <Input
            type="password"
            value={anthropicApiKey}
            onChange={e => setAnthropicApiKey(e.target.value)}
            placeholder="Enter Anthropic API Key (optional)"
            theme={theme}
          />
          <HelpText theme={theme}>Required for Claude models (claude-*). Get your key at <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer">Anthropic Console</a></HelpText>
        </FormGroup>
        
        <FormGroup>
          <Label theme={theme}>
            OpenAI API Key
          </Label>
          <Input
            type="password"
            value={openaiApiKey}
            onChange={e => setOpenaiApiKey(e.target.value)}
            placeholder="Enter OpenAI API Key (optional)"
            theme={theme}
          />
          <HelpText theme={theme}>Required for OpenAI models (gpt-*, o*). Get your key at <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">OpenAI Platform</a></HelpText>
        </FormGroup>
        
        <SaveButton 
          onClick={handleSave}
          disabled={!geminiApiKey.trim()} // Gemini API Key is mandatory
        >
          Save Configuration
        </SaveButton>
      </ModalContainer>
    </ModalOverlay>
  );
};

export default ConfigModal;
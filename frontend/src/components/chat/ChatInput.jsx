import React, { useState, useRef, useEffect } from 'react';
import { FiSend, FiLoader, FiPlus } from 'react-icons/fi';

const ChatInput = ({ onSendMessage, disabled, placeholder, isLoading }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);
  
  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  return (
    <div className="input-container">
      <div className="input-wrapper">
        <form className="input-form" onSubmit={handleSubmit} style={{width: '100%', display: 'flex', alignItems: 'flex-end'}}>
          <textarea
            className="input-textarea"
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
          />
          <div className="input-actions">
            <button 
              className="input-button"
              type="button" 
              disabled={disabled}
              aria-label="Add attachment"
            >
              <FiPlus />
            </button>
            <button 
              className={`input-button send ${message.trim().length > 0 ? 'active' : ''}`}
              type="submit" 
              disabled={!message.trim() || disabled}
              aria-label="Send message"
            >
              {isLoading ? (
                <FiLoader className="loading-icon" style={{animation: 'spin 1s linear infinite'}} />
              ) : (
                <FiSend />
              )}
            </button>
          </div>
        </form>
      </div>
      <div className="input-footer">
        opendeepwiki may produce inaccurate information about repositories or code, but less then a llm without opendeepwiki.
      </div>
    </div>
  );
};

export default ChatInput;
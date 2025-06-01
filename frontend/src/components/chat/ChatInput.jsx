import React, { useState, useRef, useEffect } from 'react';
import { FiSend, FiLoader, FiPlus, FiPaperclip } from 'react-icons/fi';

const ChatInput = ({ onSendMessage, disabled, placeholder, isLoading }) => {
  const [message, setMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
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
    if (message.trim() && !disabled && !isLoading) {
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
  
  const handleFocus = () => {
    setIsFocused(true);
  };
  
  const handleBlur = () => {
    setIsFocused(false);
  };
  
  const isMessageValid = message.trim().length > 0;
  
  return (
    <div className="input-container">
      <div className="input-wrapper">
        <form className="input-form" onSubmit={handleSubmit}>
          <button 
            className="input-button attachment-button"
            type="button" 
            disabled={disabled}
            aria-label="Add attachment"
            title="Add attachment (Coming soon)"
            style={{ opacity: 0.5 }} // Temporarily disabled
          >
            <FiPaperclip size={16} />
          </button>
          
          <textarea
            className="input-textarea"
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            rows={1}
            style={{
              borderRadius: '1rem',
              transition: 'all 0.15s ease-out',
            }}
          />
          
          <button 
            className={`input-button send ${isMessageValid && !disabled && !isLoading ? 'active' : ''}`}
            type="submit" 
            disabled={!isMessageValid || disabled || isLoading}
            aria-label={isLoading ? "Sending..." : "Send message"}
            title={isLoading ? "Sending..." : "Send message"}
            style={{
              transform: isMessageValid && !disabled && !isLoading ? 'scale(1.05)' : 'scale(1)',
              transition: 'all 0.15s ease-out',
            }}
          >
            {isLoading ? (
              <FiLoader size={16} className="loading-icon" />
            ) : (
              <FiSend size={16} />
            )}
          </button>
        </form>
      </div>
      
      <div className="input-footer">
        <span style={{ opacity: 0.7 }}>
          opendeepwiki can make mistakes. Consider checking important information.
        </span>
      </div>
    </div>
  );
};

export default ChatInput;
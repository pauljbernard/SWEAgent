import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiUser, FiCpu, FiCopy, FiCheck, FiInfo } from 'react-icons/fi';

const ChatMessages = ({ messages }) => {
  const [hoveredMessage, setHoveredMessage] = useState(null);
  const [copiedMessage, setCopiedMessage] = useState(null);
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);
  const [userScrolled, setUserScrolled] = useState(false);
  const prevMessagesLengthRef = useRef(messages.length);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    // Only auto-scroll if new messages were added and user hasn't manually scrolled up
    if (messages.length > prevMessagesLengthRef.current && !userScrolled) {
      scrollToBottom();
    }
    prevMessagesLengthRef.current = messages.length;
  }, [messages, userScrolled]);
  
  // Function to scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  // Handle scroll events to detect when user manually scrolls
  const handleScroll = (e) => {
    const container = e.target;
    const isScrolledUp = container.scrollHeight - container.scrollTop - container.clientHeight > 100;
    
    if (isScrolledUp) {
      setUserScrolled(true);
    } else {
      // If user scrolls back to bottom, reset the userScrolled flag
      setUserScrolled(false);
    }
  };
  
  const copyToClipboard = (text, index) => {
    // Create a temporary textarea element
    const textarea = document.createElement('textarea');
    textarea.value = text;
    
    // Make the textarea out of viewport
    textarea.style.position = 'fixed';
    textarea.style.left = '-999999px';
    textarea.style.top = '-999999px';
    
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    
    let success = false;
    try {
      // Execute the copy command
      success = document.execCommand('copy');
      if (success) {
        setCopiedMessage(index);
        setTimeout(() => setCopiedMessage(null), 2000);
      } else {
        console.error('Failed to copy text with execCommand');
        // Fallback to clipboard API
        navigator.clipboard.writeText(text).then(() => {
          setCopiedMessage(index);
          setTimeout(() => setCopiedMessage(null), 2000);
        }).catch(err => {
          console.error('Failed to copy text with clipboard API: ', err);
        });
      }
    } catch (err) {
      console.error('Failed to copy text: ', err);
      // Fallback to clipboard API
      navigator.clipboard.writeText(text).then(() => {
        setCopiedMessage(index);
        setTimeout(() => setCopiedMessage(null), 2000);
      }).catch(err => {
        console.error('Failed to copy text with clipboard API: ', err);
      });
    } finally {
      // Clean up
      document.body.removeChild(textarea);
    }
  };
  
  return (
    <div ref={containerRef} onScroll={handleScroll} className="messages-container">
      {messages.map((message, index) => (
        <div 
          key={index}
          className={`message-row ${message.role}`}
          onMouseEnter={() => setHoveredMessage(index)}
          onMouseLeave={() => setHoveredMessage(null)}
        >
          {message.role === 'system' ? (
            // System message (notification)
            <div className="message-container">
              <div className="message-content">
                <FiInfo size={14} style={{marginRight: '8px'}} />
                {message.content}
              </div>
            </div>
          ) : (
            // Regular user or assistant message
            <>
              <div className="message-container">
                <div className={`message-avatar ${message.role}`}>
                  {message.role === 'user' ? <FiUser size={14} /> : <FiCpu size={14} />}
                </div>
                
                <div className="message-content">
                  <ReactMarkdown
                    components={{
                      code({node, inline, className, children, ...props}) {
                        const match = /language-(\w+)/.exec(className || '');
                        if (!inline && match) {
                          const language = match[1];
                          return (
                            <div>
                              <div className="code-header">
                                <span>{language}</span>
                                <div className="code-actions">
                                  <button 
                                    className="code-action-button"
                                    onClick={() => copyToClipboard(String(children), `code-${index}`)}
                                  >
                                    {copiedMessage === `code-${index}` ? (
                                      <>
                                        <FiCheck size={14} style={{marginRight: '4px'}} />
                                        Copied!
                                      </>
                                    ) : (
                                      <>
                                        <FiCopy size={14} style={{marginRight: '4px'}} />
                                        Copy
                                      </>
                                    )}
                                  </button>
                                </div>
                              </div>
                              <SyntaxHighlighter
                                style={vscDarkPlus}
                                language={language}
                                PreTag="div"
                                {...props}
                              >
                                {String(children)}
                              </SyntaxHighlighter>
                            </div>
                          );
                        }
                        return (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      }
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>
              
              {message.role === 'assistant' && (
                <div className={`message-actions-container ${(hoveredMessage === index || copiedMessage === index) ? 'visible' : ''}`}>
                  <div className="message-actions">
                    <button 
                      className="message-action-button"
                      onClick={() => copyToClipboard(message.content, index)}
                      aria-label="Copy message"
                      title="Copy to clipboard"
                    >
                      {copiedMessage === index ? (
                        <>
                          <FiCheck size={14} />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <FiCopy size={14} />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      ))}
      <div ref={messagesEndRef} style={{ height: '1px', width: '100%' }} />
    </div>
  );
};

export default ChatMessages;
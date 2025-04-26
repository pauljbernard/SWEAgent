import React from 'react';
import { render, screen } from '@testing-library/react';
import ChatArea from './ChatArea';

describe('ChatArea', () => {
  test('renders empty state when no messages', () => {
    render(
      <ChatArea
        leftSidebarVisible={true}
        rightSidebarVisible={false}
        toggleLeftSidebar={() => {}}
        toggleRightSidebar={() => {}}
        chatHistory={[]}
        onSendMessage={() => {}}
        repoParams={{ repo_name: '', cache_id: '' }}
        isLoading={false}
      />
    );
    
    expect(screen.getByText(/What can I help with?/i)).toBeInTheDocument();
    expect(screen.getByText(/Initialize a repository from the sidebar to get started/i)).toBeInTheDocument();
  });
  
  test('renders with repository info', () => {
    render(
      <ChatArea
        leftSidebarVisible={true}
        rightSidebarVisible={false}
        toggleLeftSidebar={() => {}}
        toggleRightSidebar={() => {}}
        chatHistory={[]}
        onSendMessage={() => {}}
        repoParams={{ repo_name: 'test-repo', cache_id: 'test-cache' }}
        isLoading={false}
      />
    );
    
    expect(screen.getByText(/opendeepwiki - test-repo/i)).toBeInTheDocument();
    expect(screen.getByText(/Ask me anything about the test-repo repository/i)).toBeInTheDocument();
  });
});
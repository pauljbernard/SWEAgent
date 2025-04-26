import React from 'react';
import styled from 'styled-components';
import { FiX, FiGithub, FiCode, FiFileText, FiInfo } from 'react-icons/fi';

const SidebarContainer = styled.div`
  width: var(--right-sidebar-width);
  height: 100vh;
  background-color: ${props => props.theme === 'dark' ? 'var(--sidebar-bg-dark)' : '#f7f7f8'};
  border-left: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  overflow-y: auto;
  transition: transform 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  position: absolute;
  right: 0;
  top: 0;
  transform: ${props => props.visible ? 'translateX(0)' : 'translateX(100%)'};
`;

const SidebarHeader = styled.div`
  padding: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
`;

const HeaderTitle = styled.h2`
  font-size: 1rem;
  font-weight: 500;
  margin: 0;
  flex: 1;
  text-align: center;
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

const SectionTitle = styled.h3`
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

const InfoCard = styled.div`
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  background-color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'};
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-sm);
`;

const InfoItem = styled.div`
  margin-bottom: var(--spacing-sm);
  display: flex;
  align-items: flex-start;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const InfoIcon = styled.div`
  margin-right: var(--spacing-sm);
  color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)'};
  margin-top: 2px;
`;

const InfoContent = styled.div`
  flex: 1;
`;

const InfoLabel = styled.div`
  font-weight: 600;
  margin-bottom: 2px;
`;

const InfoValue = styled.div`
  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
  word-break: break-all;
  color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)'};
`;

const EmptyState = styled.div`
  padding: var(--spacing-md);
  text-align: center;
  color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.5)'};
  font-style: italic;
  font-size: var(--font-size-sm);
`;

const SidebarFooter = styled.div`
  padding: var(--spacing-md);
  border-top: 1px solid ${props => props.theme === 'dark' ? 'var(--border-dark)' : 'var(--border-light)'};
  font-size: var(--font-size-xs);
  color: ${props => props.theme === 'dark' ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.5)'};
  text-align: center;
`;

const RightSidebar = ({ visible, toggleSidebar, repoParams }) => {
  const isDarkMode = document.body.classList.contains('dark');
  const theme = isDarkMode ? 'dark' : 'light';
  
  const hasRepoInfo = repoParams && repoParams.repo_name;
  
  return (
    <SidebarContainer visible={visible} theme={theme}>
      <SidebarHeader theme={theme}>
        <HeaderTitle>Repository Information</HeaderTitle>
        <CloseButton onClick={toggleSidebar} theme={theme}>
          <FiX />
        </CloseButton>
      </SidebarHeader>
      
      <SidebarContent>
        <SectionTitle theme={theme}>REPOSITORY DETAILS</SectionTitle>
        
        {hasRepoInfo ? (
          <InfoCard theme={theme}>
            <InfoItem>
              <InfoIcon theme={theme}>
                <FiGithub size={16} />
              </InfoIcon>
              <InfoContent>
                <InfoLabel>Repository</InfoLabel>
                <InfoValue theme={theme}>{repoParams.repo_name}</InfoValue>
              </InfoContent>
            </InfoItem>
            
            {repoParams.cache_id && (
              <InfoItem>
                <InfoIcon theme={theme}>
                  <FiCode size={16} />
                </InfoIcon>
                <InfoContent>
                  <InfoLabel>Cache ID</InfoLabel>
                  <InfoValue theme={theme}>{repoParams.cache_id}</InfoValue>
                </InfoContent>
              </InfoItem>
            )}
          </InfoCard>
        ) : (
          <EmptyState theme={theme}>
            No repository loaded. Please initialize a repository from the left sidebar.
          </EmptyState>
        )}
        
        <SectionTitle theme={theme}>CONTEXT</SectionTitle>
        {hasRepoInfo ? (
          <InfoCard theme={theme}>
            <InfoItem>
              <InfoIcon theme={theme}>
                <FiFileText size={16} />
              </InfoIcon>
              <InfoContent>
                <InfoLabel>Documentation</InfoLabel>
                <InfoValue theme={theme}>
                  This section displays relevant context from the repository, such as documentation snippets, code examples, or other information that might be helpful for the current conversation.
                </InfoValue>
              </InfoContent>
            </InfoItem>
          </InfoCard>
        ) : (
          <EmptyState theme={theme}>
            Context will be displayed here once a repository is loaded.
          </EmptyState>
        )}
      </SidebarContent>
      
      <SidebarFooter theme={theme}>
        Powered by opendeepwiki AI
      </SidebarFooter>
    </SidebarContainer>
  );
};

export default RightSidebar;
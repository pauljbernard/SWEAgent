import React from 'react';
import styled from 'styled-components';
import { FiSun, FiMoon } from 'react-icons/fi';

const ToggleButton = styled.button`
  position: fixed;
  top: 10px;
  right: 10px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => props.isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)'};
  color: ${props => props.isDarkMode ? 'var(--text-light)' : 'var(--text-dark)'};
  border: none;
  cursor: pointer;
  transition: background-color 0.3s ease;
  z-index: 1000;
  
  &:hover {
    background: ${props => props.isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'};
  }
`;

const ThemeToggle = ({ isDarkMode, toggleDarkMode }) => {
  return (
    <ToggleButton 
      onClick={toggleDarkMode} 
      isDarkMode={isDarkMode}
      aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDarkMode ? <FiSun size={18} /> : <FiMoon size={18} />}
    </ToggleButton>
  );
};

export default ThemeToggle;
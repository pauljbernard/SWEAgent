import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock the API service
jest.mock('./services/api', () => ({
  initializeRepository: jest.fn(),
  uploadRepository: jest.fn(),
  sendMessage: jest.fn(),
}));

describe('App', () => {
  test('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText(/What can I help with?/i)).toBeInTheDocument();
  });
});
# Cahier de Charge: deeprepo-like UI for DeepRepo

## Project Overview
Create a modern, deeprepo-like user interface for the DeepRepo application that maintains all existing functionality while providing an improved user experience.

## UI Requirements

### Layout
1. **Three-panel Layout**:
   - Left sidebar (hideable): Repository information and model selection
   - Main content area: Chat interface
   - Right sidebar (hideable): Additional context or information

2. **Dark Mode Support**:
   - Dark and light theme options
   - Toggle button in the header

3. **Responsive Design**:
   - Mobile-friendly layout
   - Automatic sidebar hiding on smaller screens

### Left Sidebar
1. **Model Selection**:
   - Dropdown to select AI model
   - Options include: Gemini models, Claude models, and Custom Documentalist

2. **Repository Management**:
   - Text input for GitHub repository URL
   - "Initialize" button to load repository
   - Upload button for local repository (.zip)
   - Status message display

3. **Sidebar Toggle**:
   - Button to hide/show the sidebar
   - Collapsed state should be remembered

### Main Chat Interface
1. **Message Display**:
   - Clear distinction between user and AI messages
   - Support for markdown formatting in AI responses
   - Code syntax highlighting
   - Bubble layout similar to deeprepo

2. **Input Area**:
   - Floating input box at the bottom
   - Multi-line support with auto-expanding height
   - Send button
   - Support for keyboard shortcuts (Enter to send, Shift+Enter for new line)

3. **Chat Controls**:
   - Clear chat button
   - Copy message button
   - Optional: Message reactions

### Right Sidebar
1. **Context Display**:
   - Show relevant repository information
   - Display documentation context
   - Hideable with toggle button

2. **Additional Tools**:
   - Search functionality
   - Optional: File browser

## Functional Requirements

1. **Chat Functionality**:
   - Maintain all existing chat functionality from current implementation
   - Use the `respond` function from front_init_repo.py
   - Support for conversation history

2. **Repository Initialization**:
   - Support for GitHub repository URLs
   - Support for local repository upload via .zip
   - Use existing `init_repo` and `handle_zip_upload` functions

3. **Model Selection**:
   - Allow switching between different AI models
   - Special handling for "Custom Documentalist" model

## Technical Requirements

1. **Frontend Technologies**:
   - React.js for UI components
   - CSS modules or styled-components for styling
   - Responsive design with media queries

2. **Backend Integration**:
   - Maintain compatibility with existing Python backend
   - Use API endpoints for communication

3. **Performance Considerations**:
   - Optimize for fast loading and rendering
   - Efficient handling of long conversations

## Design Guidelines

1. **Visual Style**:
   - Clean, minimal interface similar to deeprepo
   - Dark background for dark mode
   - Light background for light mode
   - Consistent color scheme

2. **Typography**:
   - Sans-serif font for readability
   - Monospace font for code blocks
   - Appropriate font sizes for different screen sizes

3. **Animations**:
   - Subtle transitions for sidebar toggling
   - Loading indicators for API requests

## Implementation Plan

1. **Setup React Project**:
   - Initialize React application in the frontend directory
   - Configure build process

2. **Create Core Components**:
   - Layout components (App, Sidebar, ChatArea)
   - Chat components (MessageList, InputBox)
   - UI controls (Buttons, Dropdowns)

3. **Implement API Integration**:
   - Connect to existing backend endpoints
   - Handle authentication if needed

4. **Style and Polish**:
   - Implement responsive design
   - Add animations and transitions
   - Test on different devices and browsers

5. **Testing and Refinement**:
   - User testing
   - Performance optimization
   - Bug fixes
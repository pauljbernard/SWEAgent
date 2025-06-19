# Presentation Tier Overview

This document summarizes the user interface implementation found in the `frontend` directory.

## Application Structure

- **`App.jsx`** – top-level component responsible for global state and layout. It renders:
  - The left sidebar containing repository and conversation management controls.
  - The main content area with header, message history and input field.
  - A configuration modal for API keys.
- **`services/api.js`** – wrapper around HTTP calls used by the UI for repository management and chat generation.
- **Component groups**:
  - **chat/** – ChatMessages, ChatInput and ChatArea (legacy) components.
  - **sidebar/** – LeftSidebar, RightSidebar and ConfigModal components.
  - **layout/** – ThemeToggle component.
  - **RepositoryManager.jsx** – complex control for multi‑repository actions.

## Layout

The UI mimics ChatGPT’s dark theme and uses CSS variables defined in `styles/opendeepwiki-theme.css`.

- The root layout (`.app-container`) displays a fixed width left sidebar (260px) and a main content region. A right sidebar may also slide in.
- The header shows the current repository name and a “Share” action button.
- Chat messages fill most of the page height. When there are no messages an empty state is shown describing how to initialize a repository.
- The chat input sticks to the bottom of the page and includes an attachment button placeholder and a send button.

## Components

### ChatMessages

- Accepts an array of message objects with `role` (`user`, `assistant`, `system`) and `content` fields.
- Uses ReactMarkdown to render markdown with Prism syntax highlighting for code blocks.
- Shows an icon avatar per message role and provides copy buttons for both full messages and for individual code blocks.
- Automatically scrolls to the newest message unless the user scrolls upward.

### ChatInput

- Contains a growing textarea bound to local state.
- Enter sends the message (Shift+Enter inserts newline).
- Disabled while a request is in progress or until a repository is initialized.
- Displays a footer notice that the assistant may produce incorrect information.

### RepositoryManager

- Lists all known repositories, allowing the user to activate/deactivate each.
- Provides controls to initialize by URL, upload a zip archive or remove repositories.
- Shows loading indicators and success/error messages during asynchronous actions.
- Tracks which repositories are active for the conversation.

### LeftSidebar

- Wraps RepositoryManager and also exposes model selection and API configuration entry points.
- Contains a conversation list for each repository with buttons to delete or switch conversations.
- Appears fixed on the left and can be collapsed via the close icon or menu button.

### RightSidebar

- Displays repository details (repository name, cache ID) and a placeholder context panel.
- Collapses/expands from the right edge of the screen.

### ConfigModal

- Modal overlay used to collect API keys for different model providers.
- Writes keys to `localStorage` and passes them back to `App` through a callback.
- The Gemini key is mandatory; OpenAI and Anthropic keys are optional.

## Workflow Summary

1. User opens the application (served via Vite). The page loads with the left sidebar visible.
2. User initializes a repository via URL or zip upload from the sidebar. Successful initialization stores repository parameters and populates the repository list.
3. User can open the configuration modal to save API keys. These keys are used when sending chat messages.
4. Messages entered into the chat input are sent through `api.sendMessage` along with prior chat history and the selected model. Responses stream back and populate the chat history.
5. Conversations per repository are stored in local storage. Users can create a new chat, switch between conversations or delete them via the conversation list in the sidebar.
6. The right sidebar (Repository Information) may be toggled to show details about the active repository and potential context snippets.

## Styling and Theming

- Base CSS resides in `styles/opendeepwiki-theme.css` which closely matches ChatGPT’s design. Global variables drive colors, spacing and font sizes.
- Additional rules in `styles/opendeepwiki.css` define markdown rendering, code block appearance and responsive adjustments.
- The body is forced into dark mode via a `dark` class on application mount.


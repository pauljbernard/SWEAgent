# opendeepwiki Frontend

A modern, opendeepwiki-like user interface for the opendeepwiki application.

## Features

- Modern, responsive UI with a design similar to opendeepwiki
- Dark and light mode support
- Hideable sidebars for repository information and context
- Markdown rendering with syntax highlighting for code blocks
- Support for repository initialization via URL or zip upload
- Integration with the existing opendeepwiki backend

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── chat/        # Chat-related components
│   │   ├── layout/      # Layout components
│   │   └── sidebar/     # Sidebar components
│   ├── services/        # API services
│   ├── styles/          # Global styles
│   ├── adapter.py       # Python adapter for backend integration
│   ├── App.jsx          # Main application component
│   └── main.jsx         # Entry point
├── CAHIER_DE_CHARGE.md  # Project specifications
├── index.html           # HTML template
├── package.json         # Dependencies and scripts
├── run.sh               # Script to run both frontend and adapter
└── vite.config.js       # Vite configuration
```

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the development server:
   ```bash
   ./run.sh
   ```

   This will start both the Vite development server and the Flask adapter.

3. Open your browser and navigate to `http://localhost:53530`.

## Building for Production

To build the frontend for production:

```bash
npm run build
```

The built files will be in the `dist` directory.

## Technologies Used

- React.js for UI components
- Styled Components for styling
- React Markdown for rendering markdown
- React Syntax Highlighter for code highlighting
- Vite for build tooling
- Flask for the backend adapter
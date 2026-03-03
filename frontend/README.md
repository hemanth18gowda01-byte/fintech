# FinTrack Frontend

This React application provides the budgeting dashboard, charts, and AI
chatbot described in the long snippet included earlier.

## Setup

1. Navigate to the `frontend` folder:

   ```bash
   cd frontend
   npm install
   npm start
   ```

2. The development server will run on `http://localhost:3000`. Make sure the
   Flask backend is running (default `http://localhost:5000`) and set the
   appropriate base URL in the frontend code (e.g. using an environment
   variable).

3. Replace the placeholder AI API key in the backend or configure the
   `/ai-insights` proxy endpoint.


## Source code

- `src/App.js` contains the main application logic. You can paste the
  complete snippet from your previous message into this file, starting from
  the first `import` line and ending at the bottom of the component code.

- Additional components may be split into separate files (e.g.,
  `Navbar.js`, `Dashboard.js`) for maintainability.

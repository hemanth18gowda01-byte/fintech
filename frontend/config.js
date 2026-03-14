// API Configuration
// Replace this URL with your deployed backend URL
const API_BASE_URL = 'https://your-backend-url.railway.app'; // Change this after deploying backend

// Or use environment-based configuration:
// const API_BASE_URL = window.location.hostname === 'localhost' 
//   ? 'http://localhost:5000' 
//   : 'https://your-backend-url.railway.app';

// OpenAI API Key (Replace with your key or use backend proxy)
const OPENAI_API_KEY = 'your-openai-api-key-here';

// Export for use in index.html
window.API_CONFIG = {
  BASE_URL: API_BASE_URL,
  OPENAI_KEY: OPENAI_API_KEY
};

// API Configuration
// Replace this URL with your deployed backend URL
const API_BASE_URL = ' https://fintech-2-i83q.onrender.com'; // Change this after deploying backend

// Or use environment-based configuration:
// const API_BASE_URL = window.location.hostname === 'localhost' 
//   ? 'http://localhost:5000' 
//   : 'https://fintech-2-i83q.onrender.com';

// OpenAI API Key (Replace with your key or use backend proxy)
const OPENAI_API_KEY = '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';

// Export for use in index.html
window.API_CONFIG = {
  BASE_URL: API_BASE_URL,
  OPENAI_KEY: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
};

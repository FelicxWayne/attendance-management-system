import axios from 'axios';

export const TOKEN_KEY = 'access_token';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach Bearer token if present
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      delete config.headers.Authorization;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 Unauthorized globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const originalRequestUrl = error.config?.url || '';

      // Do not trigger global redirect for login failures; let the login form handle the error
      if (!originalRequestUrl.includes('/auth/login')) {
        localStorage.removeItem(TOKEN_KEY);
        // Only redirect if not already on the login page to prevent loops
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    // Normal 400, 403, 404, 409, etc. errors are passed through to callers
    return Promise.reject(error);
  }
);

export default apiClient;

import apiClient from './client';

/**
 * Authenticates user credentials against the FastAPI backend.
 * @param {{ username: string, password: string }} credentials
 * @returns {Promise<{ access_token: string, token_type: string }>}
 */
export async function loginApi({ username, password }) {
  const response = await apiClient.post('/auth/login', { username, password });
  return response.data;
}

/**
 * Retrieves profile information for the currently authenticated user.
 * @returns {Promise<{ id: number, username: string, role: string, created_at: string }>}
 */
export async function getMeApi() {
  const response = await apiClient.get('/auth/me');
  return response.data;
}

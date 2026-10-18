import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const apiClient = axios.create({
  baseURL: baseURL ?? '',
  timeout: 60000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use((response) => response, (error: unknown) => {
  if (axios.isAxiosError(error) && error.response?.status === 401) {
    window.dispatchEvent(new Event('support-agent:session-expired'));
  }
  return Promise.reject(error);
});

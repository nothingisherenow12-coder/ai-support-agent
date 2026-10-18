export function getApiErrorMessage(err: unknown, fallback: string): string {
  if (typeof err === 'object' && err !== null) {
    const e = err as {
      response?: { data?: { detail?: unknown }; status?: number };
      message?: unknown;
    };
    if (typeof e.response?.data?.detail === 'string') return e.response.data.detail;
    if (typeof e.message === 'string' && e.message.includes('Network Error')) {
      return 'Backend is unreachable. Start FastAPI on the configured VITE_API_BASE_URL.';
    }
    if (typeof e.message === 'string' && e.message.length < 200) return e.message;
  }
  return fallback;
}

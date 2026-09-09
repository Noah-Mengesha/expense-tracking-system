const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  if (response.status === 204) return null;

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed with status ${response.status}`);
  }
  return payload;
}

export const api = {
  getCategories: () => request('/categories'),
  getExpenses: (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== '' && value !== null && value !== undefined) params.set(key, value);
    });
    const query = params.toString();
    return request(`/expenses${query ? `?${query}` : ''}`);
  },
  getSummary: () => request('/summary'),
  createExpense: (expense) => request('/expenses', { method: 'POST', body: JSON.stringify(expense) }),
  updateExpense: (id, expense) => request(`/expenses/${id}`, { method: 'PUT', body: JSON.stringify(expense) }),
  deleteExpense: (id) => request(`/expenses/${id}`, { method: 'DELETE' }),
};

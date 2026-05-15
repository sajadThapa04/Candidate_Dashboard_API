const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { token, ...options } = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return null;
  }

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(formatApiError(payload.detail), response.status);
  }

  return payload;
}

function formatApiError(detail) {
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join(" ");
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }
  return "Request failed";
}

export const api = {
  login(credentials) {
    return request("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  },

  register(payload) {
    return request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  listCandidates(token, filters) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        params.set(key, value);
      }
    });
    return request(`/candidates?${params.toString()}`, { token });
  },

  getCandidate(token, id) {
    return request(`/candidates/${id}`, { token });
  },

  submitScore(token, id, payload) {
    return request(`/candidates/${id}/scores`, {
      token,
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  generateSummary(token, id) {
    return request(`/candidates/${id}/summary`, {
      token,
      method: "POST",
    });
  },

  updateCandidate(token, id, payload) {
    return request(`/candidates/${id}`, {
      token,
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
};

export { API_BASE_URL };

/**
 * TaskFlow API Client
 * Manages HTTP communication, session tokens, and automatic 401 redirection.
 */

const API = (() => {
  const TOKEN_KEY = "taskflow_auth_token";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
  }

  function setToken(token, persist = true) {
    if (persist) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      sessionStorage.setItem(TOKEN_KEY, token);
    }
  }

  function removeToken() {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
  }

  let onUnauthorizedCallback = null;

  function onUnauthorized(callback) {
    onUnauthorizedCallback = callback;
  }

  async function request(endpoint, options = {}) {
    const url = endpoint;
    const headers = options.headers || {};

    // Attach Bearer token if present
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(options.body);
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 Session Expiration / Unauthorized
      if (response.status === 401) {
        removeToken();
        if (typeof onUnauthorizedCallback === "function") {
          onUnauthorizedCallback();
        }
        const errorData = await response.json().catch(() => ({}));
        throw { status: 401, ...errorData };
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return null;
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw { status: response.status, ...data };
      }

      return data;
    } catch (err) {
      if (!err.status) {
        // Network or fetch failure
        throw { status: 0, error: "Unable to reach server. Please check your internet connection." };
      }
      throw err;
    }
  }

  return {
    getToken,
    setToken,
    removeToken,
    onUnauthorized,

    // Auth
    async register(email, password, name) {
      return request("/api/auth/register", {
        method: "POST",
        body: { email, password, name },
      });
    },

    async login(email, password, persist = true) {
      const res = await request("/api/auth/login", {
        method: "POST",
        body: { email, password },
      });
      if (res && res.token) {
        setToken(res.token, persist);
      }
      return res;
    },

    async logout() {
      try {
        await request("/api/auth/logout", { method: "POST" });
      } finally {
        removeToken();
      }
    },

    async getMe() {
      return request("/api/auth/me", { method: "GET" });
    },

    async changePassword(oldPassword, newPassword) {
      return request("/api/auth/change-password", {
        method: "POST",
        body: { oldPassword, newPassword },
      });
    },

    // Tasks
    async getTasks(params = {}) {
      const query = new URLSearchParams();
      if (params.status && params.status !== "all") query.append("status", params.status);
      if (params.priority) query.append("priority", params.priority);
      if (params.q) query.append("q", params.q);
      if (params.sort) query.append("sort", params.sort);
      if (params.order) query.append("order", params.order);

      const qs = query.toString();
      return request(`/api/tasks${qs ? `?${qs}` : ""}`, { method: "GET" });
    },

    async createTask(taskData) {
      return request("/api/tasks", {
        method: "POST",
        body: taskData,
      });
    },

    async getTask(taskId) {
      return request(`/api/tasks/${taskId}`, { method: "GET" });
    },

    async patchTask(taskId, updates) {
      return request(`/api/tasks/${taskId}`, {
        method: "PATCH",
        body: updates,
      });
    },

    async deleteTask(taskId) {
      return request(`/api/tasks/${taskId}`, {
        method: "DELETE",
      });
    },
  };
})();

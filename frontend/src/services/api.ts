/**
 * API Service Configuration
 * Centralized axios instance with interceptors for authentication
 */
import axios, { AxiosInstance, AxiosError } from "axios";

// API base URL from environment variable
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Create axios instance with default configuration
 */
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Request interceptor to add authentication token
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor to handle errors globally
 */
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem("auth_token");
      window.location.href = "/login";
    }

    // Extract error message
    const errorMessage =
      (error.response?.data as any)?.detail ||
      (error.response?.data as any)?.error ||
      (error.response?.data as any)?.message ||
      error.message ||
      "An unexpected error occurred";

    return Promise.reject(new Error(errorMessage));
  }
);

export default api;

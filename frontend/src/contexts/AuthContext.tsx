import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

/**
 * Authentication context types
 */
interface User {
  id: string;
  email: string;
  name?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setToken: (token: string) => void;
}

/**
 * Authentication Context
 * Manages user authentication state and JWT tokens
 * 
 * Validates: Requirements 20.1
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

// Configure axios defaults
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
axios.defaults.baseURL = API_BASE_URL;

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token from localStorage on mount and fetch user info
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      setTokenState(storedToken);
      // Fetch user info with the stored token
      fetchUserInfo(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch current user information
   */
  const fetchUserInfo = async (authToken: string) => {
    try {
      const response = await axios.get('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      
      setUser({
        id: response.data._id,
        email: response.data.email,
        name: response.data.name,
      });
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      // Token might be invalid, clear it
      localStorage.removeItem('auth_token');
      setTokenState(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Login function
   * Authenticates user and stores JWT token
   */
  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await axios.post('/api/auth/login', { 
        email, 
        password 
      });
      
      const { access_token } = response.data;

      // Store token in localStorage
      localStorage.setItem('auth_token', access_token);
      setTokenState(access_token);
      
      // Fetch user info
      await fetchUserInfo(access_token);
    } catch (error: any) {
      console.error('Login failed:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.error || 
                          'Login failed. Please check your credentials.';
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Logout function
   * Clears authentication state and removes token
   */
  const logout = (): void => {
    localStorage.removeItem('auth_token');
    setTokenState(null);
    setUser(null);
  };

  /**
   * Set token function
   * Updates token state and localStorage
   */
  const setToken = (newToken: string): void => {
    localStorage.setItem('auth_token', newToken);
    setTokenState(newToken);
  };

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    logout,
    setToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Custom hook to use authentication context
 * Throws error if used outside AuthProvider
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;

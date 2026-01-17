import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Navigation component with header and menu
 * Provides links to main sections of the application
 */
const Navigation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const navLinkClass = (path: string) => {
    const baseClass = "px-3 py-2 rounded-md text-sm font-medium transition-colors";
    return isActive(path)
      ? `${baseClass} bg-blue-700 text-white`
      : `${baseClass} text-gray-300 hover:bg-blue-600 hover:text-white`;
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-blue-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <span className="text-white text-2xl font-bold">SVA-Chatbot</span>
            </Link>
          </div>

          {/* Navigation links */}
          <div className="flex items-center space-x-4">
            <Link to="/" className={navLinkClass('/')}>
              Home
            </Link>
            <Link to="/projects" className={navLinkClass('/projects')}>
              Projects
            </Link>
          </div>

          {/* User menu */}
          <div className="flex items-center space-x-4">
            {isAuthenticated && user ? (
              <>
                <span className="text-gray-300 text-sm">
                  {user.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;

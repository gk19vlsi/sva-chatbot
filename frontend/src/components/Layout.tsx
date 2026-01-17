import React from 'react';
import { Outlet } from 'react-router-dom';
import Navigation from './Navigation';

/**
 * Main layout component that wraps all pages
 * Provides consistent header, navigation, and content structure
 */
const Layout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;

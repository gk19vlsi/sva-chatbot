import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import Projects from './pages/Projects';
import Upload from './pages/Upload';
import Assertions from './pages/Assertions';
import Login from './pages/Login';

/**
 * Main App component
 * Sets up routing, authentication, and layout structure
 * 
 * Validates: Requirements 20.1
 */
function App() {
  return (
    <AuthProvider>
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />

          {/* Protected routes */}
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route
              path="projects"
              element={
                <ProtectedRoute>
                  <Projects />
                </ProtectedRoute>
              }
            />
            <Route
              path="projects/:projectId/upload"
              element={
                <ProtectedRoute>
                  <Upload />
                </ProtectedRoute>
              }
            />
            <Route
              path="projects/:projectId/assertions"
              element={
                <ProtectedRoute>
                  <Assertions />
                </ProtectedRoute>
              }
            />
            {/* Legacy upload route - redirects to project selection */}
            <Route
              path="upload"
              element={
                <ProtectedRoute>
                  <Upload />
                </ProtectedRoute>
              }
            />
            {/* Legacy assertions route - redirects to project selection */}
            <Route
              path="assertions"
              element={
                <ProtectedRoute>
                  <Assertions />
                </ProtectedRoute>
              }
            />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;

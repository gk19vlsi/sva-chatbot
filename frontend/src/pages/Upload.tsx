import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import api from '../services/api';

interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
}

/**
 * Upload page component
 * Handles file uploads for specifications and RTL designs
 * 
 * Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5
 */
const Upload: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [notifications, setNotifications] = useState<Array<{ type: 'success' | 'error'; message: string }>>([]);
  const [projectName, setProjectName] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [hasSpecFiles, setHasSpecFiles] = useState(false);
  const [hasRtlFiles, setHasRtlFiles] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const navigate = useNavigate();

  // Fetch project details or project list
  useEffect(() => {
    if (projectId) {
      fetchProjectDetails();
    } else {
      fetchProjects();
    }
  }, [projectId]);

  const fetchProjectDetails = async () => {
    if (!projectId) return;
    
    try {
      const response = await api.get(`/api/projects/${projectId}`);
      setProjectName(response.data.name);
    } catch (error) {
      console.error('Failed to fetch project details:', error);
      addNotification('error', 'Failed to load project details');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await api.get('/api/projects');
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      addNotification('error', 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleProjectSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newProjectId = e.target.value;
    setSelectedProjectId(newProjectId);
    if (newProjectId) {
      navigate(`/projects/${newProjectId}/upload`);
    }
  };

  const addNotification = (type: 'success' | 'error', message: string) => {
    setNotifications(prev => [...prev, { type, message }]);
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.slice(1));
    }, 5000);
  };

  const handleUploadComplete = (fileType: string) => (_fileId: string) => {
    addNotification('success', `${fileType} file uploaded successfully!`);
    
    // Update file status flags
    if (fileType === 'Specification') {
      setHasSpecFiles(true);
    } else if (fileType === 'RTL') {
      setHasRtlFiles(true);
    }
  };

  const handleUploadError = (fileType: string) => (error: Error) => {
    addNotification('error', `${fileType} upload failed: ${error.message}`);
  };

  const handleGenerateAssertions = async () => {
    if (!projectId) return;

    try {
      setGenerating(true);
      addNotification('success', 'Starting assertion generation...');

      const response = await api.post(`/api/projects/${projectId}/generate-assertions`);

      addNotification('success', `Successfully generated ${response.data.assertions_generated} assertions!`);
      
      // Navigate to assertions page after a short delay
      setTimeout(() => {
        navigate(`/projects/${projectId}/assertions`);
      }, 2000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate assertions';
      addNotification('error', errorMessage);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!projectId) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-white shadow rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            Upload Files
          </h1>
          
          <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded mb-6">
            <p className="font-semibold mb-2">Select a project to upload files</p>
            <p className="text-sm">Choose an existing project from the dropdown below, or create a new project from the Projects page.</p>
          </div>

          {projects.length > 0 ? (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Project
              </label>
              <select
                value={selectedProjectId}
                onChange={handleProjectSelect}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
              >
                <option value="">-- Choose a project --</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name} {project.description ? `- ${project.description}` : ''}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">No projects found. Create a project first.</p>
              <button
                onClick={() => navigate('/projects')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Go to Projects
              </button>
            </div>
          )}

          <div className="mt-6 border-t pt-6">
            <button
              onClick={() => navigate('/projects')}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              ← Back to Projects
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="bg-white shadow rounded-lg p-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Upload Files
          </h1>
          {projectName && (
            <p className="text-gray-600 mt-2">
              Project: <span className="font-semibold">{projectName}</span>
            </p>
          )}
        </div>

        {/* Notifications */}
        {notifications.length > 0 && (
          <div className="mb-6 space-y-2">
            {notifications.map((notification, index) => (
              <div
                key={index}
                className={`
                  p-4 rounded-lg
                  ${notification.type === 'success'
                    ? 'bg-green-50 border border-green-200 text-green-800'
                    : 'bg-red-50 border border-red-200 text-red-800'
                  }
                `}
              >
                {notification.message}
              </div>
            ))}
          </div>
        )}

        <div className="space-y-8">
          {/* Specification upload section */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Specification Documents
            </h2>
            <FileUpload
              fileType="specification"
              projectId={projectId}
              onUploadComplete={handleUploadComplete('Specification')}
              onUploadError={handleUploadError('Specification')}
            />
          </div>

          {/* RTL upload section */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              RTL Design Files
            </h2>
            <FileUpload
              fileType="rtl"
              projectId={projectId}
              onUploadComplete={handleUploadComplete('RTL')}
              onUploadError={handleUploadError('RTL')}
            />
          </div>
        </div>

        {/* Generate Assertions Button */}
        {hasSpecFiles && hasRtlFiles && (
          <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Ready to Generate Assertions
                </h3>
                <p className="text-sm text-gray-600">
                  You have uploaded specification and RTL files. Click the button to start generating SystemVerilog assertions.
                </p>
              </div>
              <button
                onClick={handleGenerateAssertions}
                disabled={generating}
                className="ml-6 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {generating ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    <span>Generate Assertions</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Help text */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">
            Upload Guidelines
          </h3>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li>Specification files can be in PDF, DOCX, Markdown, or plain text format</li>
            <li>RTL files should be in SystemVerilog (.sv) or Verilog (.v) format</li>
            <li>Maximum file size is 50MB per file</li>
            <li>You can upload multiple files at once</li>
            <li>Files are automatically validated before upload</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Upload;

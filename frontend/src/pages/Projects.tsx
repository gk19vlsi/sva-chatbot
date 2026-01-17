import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

interface Project {
  id: string;
  name: string;
  description: string;
  user_id: string;
  status: 'draft' | 'processing' | 'completed' | 'failed';
  created_at: string;
  metadata: {
    total_specs: number;
    total_rtl_files: number;
    total_assertions: number;
  };
}

/**
 * Projects page component
 * Lists all user projects with summary statistics
 * 
 * Requirements: 12.1, 12.2, 12.3, 12.4
 */
const Projects: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/projects');
      setProjects(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    try {
      setCreating(true);
      const response = await api.post('/api/projects', {
        name: newProjectName,
        description: newProjectDescription,
      });

      const newProject = response.data;
      setProjects([newProject, ...projects]);
      setShowCreateModal(false);
      setNewProjectName('');
      setNewProjectDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      await api.delete(`/api/projects/${projectId}`);
      setProjects(projects.filter(p => p.id !== projectId));
      setDeleteConfirm(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete project');
    }
  };

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="bg-white shadow rounded-lg p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            My Projects
          </h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
          >
            + New Project
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Loading state */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading projects...</p>
          </div>
        ) : projects.length === 0 ? (
          /* Empty state */
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
            <p className="text-gray-500 text-lg mb-4">
              No projects yet. Create your first project to get started!
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium transition-colors"
            >
              Create Project
            </button>
          </div>
        ) : (
          /* Project list */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <div
                key={project.id}
                className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg font-semibold text-gray-900 truncate flex-1">
                    {project.name}
                  </h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(project.status)}`}>
                    {project.status}
                  </span>
                </div>

                {project.description && (
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {project.description}
                  </p>
                )}

                {/* Statistics */}
                <div className="grid grid-cols-3 gap-2 mb-4 text-center">
                  <div className="bg-gray-50 rounded p-2">
                    <div className="text-2xl font-bold text-gray-900">
                      {project.metadata.total_specs}
                    </div>
                    <div className="text-xs text-gray-600">Specs</div>
                  </div>
                  <div className="bg-gray-50 rounded p-2">
                    <div className="text-2xl font-bold text-gray-900">
                      {project.metadata.total_rtl_files}
                    </div>
                    <div className="text-xs text-gray-600">RTL Files</div>
                  </div>
                  <div className="bg-gray-50 rounded p-2">
                    <div className="text-2xl font-bold text-gray-900">
                      {project.metadata.total_assertions}
                    </div>
                    <div className="text-xs text-gray-600">Assertions</div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 mb-3">
                  <button
                    onClick={() => navigate(`/projects/${project.id}/upload`)}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm font-medium transition-colors"
                  >
                    Upload Files
                  </button>
                  <button
                    onClick={() => navigate(`/projects/${project.id}/assertions`)}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm font-medium transition-colors"
                  >
                    View Assertions
                  </button>
                </div>

                <div className="flex justify-between items-center text-sm text-gray-500">
                  <span>Created {formatDate(project.created_at)}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteConfirm(project.id);
                    }}
                    className="text-red-600 hover:text-red-800 font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Create New Project
            </h2>
            <form onSubmit={handleCreateProject}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Name *
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter project name"
                  required
                />
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter project description"
                  rows={3}
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewProjectName('');
                    setNewProjectDescription('');
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  disabled={creating}
                >
                  {creating ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Delete Project?
            </h2>
            <p className="text-gray-600 mb-6">
              This will permanently delete the project and all associated specifications, RTL files, and assertions. This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteProject(deleteConfirm)}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Delete Project
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Projects;

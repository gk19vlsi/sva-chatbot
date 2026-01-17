/**
 * TraceabilityMatrix Component
 * 
 * Displays requirement-assertion traceability matrix with coverage visualization.
 * 
 * Implements Requirements 8.5
 */
import React, { useState, useEffect } from 'react';

interface Requirement {
  id: string;
  text: string;
  category: string;
}

interface Assertion {
  id: string;
  code: string;
  confidence_score: number;
  quality_score?: number;
}

interface MatrixEntry {
  requirement: Requirement;
  assertions: Assertion[];
  coverage: boolean;
}

interface TraceabilityMatrixProps {
  projectId: string;
  onRequirementClick?: (requirementId: string) => void;
  onAssertionClick?: (assertionId: string) => void;
}

export const TraceabilityMatrix: React.FC<TraceabilityMatrixProps> = ({
  projectId,
  onRequirementClick,
  onAssertionClick
}) => {
  const [matrix, setMatrix] = useState<MatrixEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterCoverage, setFilterCoverage] = useState<string>('all');

  useEffect(() => {
    fetchMatrix();
  }, [projectId]);

  const fetchMatrix = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/projects/${projectId}/traceability-matrix`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch traceability matrix');
      }

      const data = await response.json();
      setMatrix(data.matrix || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Get unique categories
  const categories = ['all', ...new Set(matrix.map(entry => entry.requirement.category))];

  // Filter matrix entries
  const filteredMatrix = matrix.filter(entry => {
    const categoryMatch = filterCategory === 'all' || entry.requirement.category === filterCategory;
    const coverageMatch = 
      filterCoverage === 'all' ||
      (filterCoverage === 'covered' && entry.coverage) ||
      (filterCoverage === 'uncovered' && !entry.coverage);
    return categoryMatch && coverageMatch;
  });

  // Calculate statistics
  const totalRequirements = matrix.length;
  const coveredRequirements = matrix.filter(e => e.coverage).length;
  const coveragePercentage = totalRequirements > 0 
    ? (coveredRequirements / totalRequirements * 100).toFixed(1)
    : '0.0';

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={fetchMatrix}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="traceability-matrix bg-white rounded-lg shadow">
      {/* Header with statistics */}
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Traceability Matrix
        </h2>
        
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">Total Requirements</p>
            <p className="text-2xl font-bold text-blue-600">{totalRequirements}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">Covered</p>
            <p className="text-2xl font-bold text-green-600">{coveredRequirements}</p>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <p className="text-sm text-gray-600">Coverage</p>
            <p className="text-2xl font-bold text-purple-600">{coveragePercentage}%</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Coverage
            </label>
            <select
              value={filterCoverage}
              onChange={(e) => setFilterCoverage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All</option>
              <option value="covered">Covered</option>
              <option value="uncovered">Uncovered</option>
            </select>
          </div>
        </div>
      </div>

      {/* Matrix table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Requirement
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Assertions
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Coverage
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredMatrix.map((entry, index) => (
              <tr
                key={entry.requirement.id || index}
                className="hover:bg-gray-50 transition-colors"
              >
                <td className="px-6 py-4">
                  <button
                    onClick={() => onRequirementClick?.(entry.requirement.id)}
                    className="text-left text-sm text-gray-900 hover:text-blue-600 hover:underline"
                  >
                    {entry.requirement.text.substring(0, 100)}
                    {entry.requirement.text.length > 100 ? '...' : ''}
                  </button>
                </td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {entry.requirement.category}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-2">
                    {entry.assertions.map((assertion, idx) => (
                      <button
                        key={assertion.id || idx}
                        onClick={() => onAssertionClick?.(assertion.id)}
                        className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 hover:bg-green-200"
                        title={`Confidence: ${(assertion.confidence_score * 100).toFixed(0)}%`}
                      >
                        Assertion {idx + 1}
                      </button>
                    ))}
                    {entry.assertions.length === 0 && (
                      <span className="text-xs text-gray-400 italic">No assertions</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  {entry.coverage ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Covered
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                      Uncovered
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredMatrix.length === 0 && (
        <div className="p-8 text-center text-gray-500">
          No requirements found matching the selected filters.
        </div>
      )}
    </div>
  );
};

export default TraceabilityMatrix;

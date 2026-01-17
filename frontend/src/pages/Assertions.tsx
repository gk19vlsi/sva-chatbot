import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import AssertionViewer, { Assertion } from '../components/AssertionViewer';
import api from '../services/api';

/**
 * Assertions page component
 * Displays generated assertions with filtering and search
 * 
 * Validates: Requirements 14.1, 14.5
 */
const Assertions: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [assertions, setAssertions] = useState<Assertion[]>([]);
  const [selectedAssertion, setSelectedAssertion] = useState<Assertion | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  // Fetch assertions on mount
  useEffect(() => {
    if (projectId) {
      fetchAssertions();
    }
  }, [projectId]);

  const fetchAssertions = async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/api/assertions/project/${projectId}`);
      
      // Transform backend data to frontend format
      const transformedAssertions: Assertion[] = response.data.assertions.map((item: any) => ({
        id: item.id || item._id,
        code: item.code,
        type: item.type,
        category: item.category,
        confidenceScore: item.confidence_score,
        qualityScore: item.quality_score,
        explanation: item.explanation,
        traceability: item.traceability ? {
          requirementText: item.traceability.requirement_text,
          rtlSignals: item.traceability.rtl_signals || [],
          rtlModule: item.traceability.rtl_module,
        } : undefined,
      }));

      setAssertions(transformedAssertions);
      if (transformedAssertions.length > 0) {
        setSelectedAssertion(transformedAssertions[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch assertions');
    } finally {
      setLoading(false);
    }
  };

  const handleExportAll = async () => {
    if (!projectId) return;

    try {
      setExporting(true);
      const response = await api.get(`/api/projects/${projectId}/export`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `assertions_${projectId}.sv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export assertions');
    } finally {
      setExporting(false);
    }
  };

  if (!projectId) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-white shadow rounded-lg p-8">
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded">
            Please select a project first to view assertions.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="bg-white shadow rounded-lg p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Generated Assertions
          </h1>
          <button 
            onClick={handleExportAll}
            disabled={exporting || assertions.length === 0}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {exporting ? 'Exporting...' : 'Export All'}
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
            <p className="mt-2 text-gray-600">Loading assertions...</p>
          </div>
        ) : assertions.length === 0 ? (
          /* Empty state */
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
            <p className="text-gray-500 text-lg">
              No assertions generated yet. Upload files and start generation!
            </p>
          </div>
        ) : (
          /* Assertions display */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Assertions list */}
            <div className="lg:col-span-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Assertions ({assertions.length})
              </h2>
              <div className="space-y-2">
                {assertions.map((assertion) => (
                  <button
                    key={assertion.id}
                    onClick={() => setSelectedAssertion(assertion)}
                    className={`
                      w-full text-left p-4 rounded-lg border transition-colors
                      ${
                        selectedAssertion?.id === assertion.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                      }
                    `}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">
                        {assertion.id}
                      </span>
                      <span className="text-xs text-gray-500">
                        {assertion.type}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {assertion.explanation}
                    </p>
                    <div className="flex items-center space-x-2 mt-2">
                      <span className="text-xs text-gray-500">
                        Confidence: {(assertion.confidenceScore * 100).toFixed(0)}%
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Selected assertion viewer */}
            <div className="lg:col-span-2">
              {selectedAssertion ? (
                <AssertionViewer assertion={selectedAssertion} readOnly={true} />
              ) : (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                  <p className="text-gray-500">
                    Select an assertion to view details
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Assertions;

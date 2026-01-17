/**
 * Dashboard Component
 * 
 * Displays project statistics, coverage charts, and quality metrics.
 * 
 * Implements Requirements 12.5, 8.5
 */
import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import TraceabilityMatrix from './TraceabilityMatrix';
import SignalDependencyGraph from './SignalDependencyGraph';

interface ProjectStatistics {
  total_specs: number;
  total_rtl_files: number;
  total_assertions: number;
  total_requirements?: number;
  covered_requirements?: number;
  coverage_percentage?: number;
}

interface CoverageByCategory {
  [category: string]: {
    total_requirements: number;
    covered_requirements: number;
    coverage_percentage: number;
    assertion_count: number;
  };
}

interface Assertion {
  id: string;
  confidence_score: number;
  quality_score?: number;
  assertion_type: string;
  category: string;
}

interface DashboardProps {
  projectId: string;
  projectName: string;
  statistics: ProjectStatistics;
  assertions?: Assertion[];
  coverageByCategory?: CoverageByCategory;
}

export const Dashboard: React.FC<DashboardProps> = ({
  projectId,
  projectName,
  statistics,
  assertions = [],
  coverageByCategory = {}
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'traceability' | 'dependencies'>('overview');
  // Calculate confidence score distribution
  const getConfidenceDistribution = () => {
    const distribution = {
      high: 0,    // >= 0.8
      medium: 0,  // 0.6 - 0.79
      low: 0      // < 0.6
    };

    assertions.forEach(assertion => {
      if (assertion.confidence_score >= 0.8) {
        distribution.high++;
      } else if (assertion.confidence_score >= 0.6) {
        distribution.medium++;
      } else {
        distribution.low++;
      }
    });

    return [
      { name: 'High (≥80%)', value: distribution.high, color: '#4CAF50' },
      { name: 'Medium (60-79%)', value: distribution.medium, color: '#FFC107' },
      { name: 'Low (<60%)', value: distribution.low, color: '#F44336' }
    ];
  };

  // Calculate quality score distribution
  const getQualityDistribution = () => {
    const distribution = {
      high: 0,
      medium: 0,
      low: 0
    };

    assertions.forEach(assertion => {
      if (assertion.quality_score !== undefined) {
        if (assertion.quality_score >= 0.8) {
          distribution.high++;
        } else if (assertion.quality_score >= 0.6) {
          distribution.medium++;
        } else {
          distribution.low++;
        }
      }
    });

    return [
      { name: 'High (≥80%)', value: distribution.high, color: '#4CAF50' },
      { name: 'Medium (60-79%)', value: distribution.medium, color: '#FFC107' },
      { name: 'Low (<60%)', value: distribution.low, color: '#F44336' }
    ];
  };

  // Prepare coverage by category data for chart
  const getCoverageByCategory = () => {
    return Object.entries(coverageByCategory).map(([category, data]) => ({
      category: category.charAt(0).toUpperCase() + category.slice(1),
      covered: data.covered_requirements,
      uncovered: data.total_requirements - data.covered_requirements,
      coverage: data.coverage_percentage
    }));
  };

  // Calculate assertion type distribution
  const getAssertionTypeDistribution = () => {
    const types: { [key: string]: number } = {};
    
    assertions.forEach(assertion => {
      types[assertion.assertion_type] = (types[assertion.assertion_type] || 0) + 1;
    });

    return Object.entries(types).map(([type, count]) => ({
      name: type.charAt(0).toUpperCase() + type.slice(1),
      value: count
    }));
  };

  const confidenceData = getConfidenceDistribution();
  const qualityData = getQualityDistribution();
  const categoryData = getCoverageByCategory();
  const typeData = getAssertionTypeDistribution();

  const coveragePercentage = statistics.coverage_percentage || 0;
  const coveredReqs = statistics.covered_requirements || 0;
  const totalReqs = statistics.total_requirements || 0;

  return (
    <div className="dashboard p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{projectName}</h1>
        <p className="text-gray-600 mt-1">Project Dashboard</p>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('traceability')}
            className={`${
              activeTab === 'traceability'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Traceability Matrix
          </button>
          <button
            onClick={() => setActiveTab('dependencies')}
            className={`${
              activeTab === 'dependencies'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Signal Dependencies
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <>
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Specifications Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Specifications</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {statistics.total_specs}
              </p>
            </div>
            <div className="bg-blue-100 rounded-full p-3">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
        </div>

        {/* RTL Files Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">RTL Files</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {statistics.total_rtl_files}
              </p>
            </div>
            <div className="bg-green-100 rounded-full p-3">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
          </div>
        </div>

        {/* Assertions Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Assertions</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {statistics.total_assertions}
              </p>
            </div>
            <div className="bg-purple-100 rounded-full p-3">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
          </div>
        </div>

        {/* Coverage Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Coverage</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {coveragePercentage.toFixed(0)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {coveredReqs} of {totalReqs} requirements
              </p>
            </div>
            <div className={`rounded-full p-3 ${
              coveragePercentage >= 80 ? 'bg-green-100' :
              coveragePercentage >= 60 ? 'bg-yellow-100' :
              'bg-red-100'
            }`}>
              <svg className={`w-8 h-8 ${
                coveragePercentage >= 80 ? 'text-green-600' :
                coveragePercentage >= 60 ? 'text-yellow-600' :
                'text-red-600'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Confidence Score Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Confidence Score Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={confidenceData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {confidenceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Quality Score Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Quality Score Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={qualityData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {qualityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Coverage by Category */}
      {categoryData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Coverage by Requirement Category
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categoryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="covered" stackId="a" fill="#4CAF50" name="Covered" />
              <Bar dataKey="uncovered" stackId="a" fill="#F44336" name="Uncovered" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Assertion Type Distribution */}
      {typeData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Assertion Type Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={typeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#2196F3" name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
        </>
      )}

      {/* Traceability Matrix Tab */}
      {activeTab === 'traceability' && (
        <TraceabilityMatrix
          projectId={projectId}
          onRequirementClick={(reqId) => console.log('Requirement clicked:', reqId)}
          onAssertionClick={(assertionId) => console.log('Assertion clicked:', assertionId)}
        />
      )}

      {/* Signal Dependencies Tab */}
      {activeTab === 'dependencies' && (
        <SignalDependencyGraph
          projectId={projectId}
          width={1200}
          height={700}
        />
      )}
    </div>
  );
};

export default Dashboard;

/**
 * Dashboard Component Tests
 * 
 * Tests chart rendering, data display, and statistics accuracy.
 * 
 * Validates Requirements 12.5, 8.5
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Dashboard from './Dashboard';

// Mock child components
vi.mock('./TraceabilityMatrix', () => ({
  default: ({ projectId }: { projectId: string }) => (
    <div data-testid="traceability-matrix">Traceability Matrix for {projectId}</div>
  )
}));

vi.mock('./SignalDependencyGraph', () => ({
  default: ({ projectId }: { projectId: string }) => (
    <div data-testid="signal-dependency-graph">Signal Graph for {projectId}</div>
  )
}));

describe('Dashboard Component', () => {
  const mockStatistics = {
    total_specs: 5,
    total_rtl_files: 3,
    total_assertions: 25,
    total_requirements: 20,
    covered_requirements: 16,
    coverage_percentage: 80
  };

  const mockAssertions = [
    {
      id: '1',
      confidence_score: 0.9,
      quality_score: 0.85,
      assertion_type: 'immediate',
      category: 'functional'
    },
    {
      id: '2',
      confidence_score: 0.75,
      quality_score: 0.7,
      assertion_type: 'concurrent',
      category: 'timing'
    },
    {
      id: '3',
      confidence_score: 0.5,
      quality_score: 0.55,
      assertion_type: 'immediate',
      category: 'functional'
    },
    {
      id: '4',
      confidence_score: 0.95,
      quality_score: 0.9,
      assertion_type: 'concurrent',
      category: 'safety'
    }
  ];

  const mockCoverageByCategory = {
    functional: {
      total_requirements: 10,
      covered_requirements: 8,
      coverage_percentage: 80,
      assertion_count: 12
    },
    timing: {
      total_requirements: 5,
      covered_requirements: 4,
      coverage_percentage: 80,
      assertion_count: 6
    },
    safety: {
      total_requirements: 5,
      covered_requirements: 4,
      coverage_percentage: 80,
      assertion_count: 7
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Statistics Cards', () => {
    it('should display project name', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });

    it('should display total specifications count', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('Specifications')).toBeInTheDocument();
    });

    it('should display total RTL files count', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('RTL Files')).toBeInTheDocument();
    });

    it('should display total assertions count', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('Assertions')).toBeInTheDocument();
    });

    it('should display coverage percentage', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      expect(screen.getByText('80%')).toBeInTheDocument();
      expect(screen.getByText('Coverage')).toBeInTheDocument();
    });

    it('should display covered and total requirements', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      expect(screen.getByText('16 of 20 requirements')).toBeInTheDocument();
    });

    it('should handle zero coverage gracefully', () => {
      const zeroStats = {
        ...mockStatistics,
        total_requirements: 0,
        covered_requirements: 0,
        coverage_percentage: 0
      };

      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={zeroStats}
        />
      );

      expect(screen.getByText('0%')).toBeInTheDocument();
    });
  });

  describe('Confidence Score Distribution', () => {
    it('should render confidence score chart', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          assertions={mockAssertions}
        />
      );

      expect(screen.getByText('Confidence Score Distribution')).toBeInTheDocument();
    });

    it('should categorize confidence scores correctly', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          assertions={mockAssertions}
        />
      );

      // High: 0.9, 0.95 = 2
      // Medium: 0.75 = 1
      // Low: 0.5 = 1
      // The chart should display these values
      expect(screen.getByText(/High.*2/)).toBeInTheDocument();
      expect(screen.getByText(/Medium.*1/)).toBeInTheDocument();
      expect(screen.getByText(/Low.*1/)).toBeInTheDocument();
    });
  });

  describe('Quality Score Distribution', () => {
    it('should render quality score chart', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          assertions={mockAssertions}
        />
      );

      expect(screen.getByText('Quality Score Distribution')).toBeInTheDocument();
    });

    it('should categorize quality scores correctly', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          assertions={mockAssertions}
        />
      );

      // High: 0.85, 0.9 = 2
      // Medium: 0.7 = 1
      // Low: 0.55 = 1
      expect(screen.getByText(/High.*2/)).toBeInTheDocument();
      expect(screen.getByText(/Medium.*1/)).toBeInTheDocument();
      expect(screen.getByText(/Low.*1/)).toBeInTheDocument();
    });

    it('should handle assertions without quality scores', () => {
      const assertionsWithoutQuality = mockAssertions.map(a => ({
        ...a,
        quality_score: undefined
      }));

      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          assertions={assertionsWithoutQuality}
        />
      );

      // Should still render the chart
      expect(screen.getByText('Quality Score Distribution')).toBeInTheDocument();
    });
  });

  describe('Coverage by Category Chart', () => {
    it('should render coverage by category chart when data is provided', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          coverageByCategory={mockCoverageByCategory}
        />
      );

      expect(screen.getByText('Coverage by Requirement Category')).toBeInTheDocument();
    });

    it('should not render coverage chart when no data is provided', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      expect(screen.queryByText('Coverage by Requirement Category')).not.toBeInTheDocument();
    });

    it('should display all categories', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          coverageByCategory={mockCoverageByCategory}
        />
      );

      // Categories should be capitalized in the chart
      expect(screen.getByText('Functional')).toBeInTheDocument();
      expect(screen.getByText('Timing')).toBeInTheDocument();
      expect(screen.getByText('Safety')).toBeInTheDocument();
    });
  });

  describe('Assertion Type Distribution Chart', () => {
    it('should render assertion type chart when assertions are provided', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          assertions={mockAssertions}
        />
      );

      expect(screen.getByText('Assertion Type Distribution')).toBeInTheDocument();
    });

    it('should not render type chart when no assertions are provided', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      expect(screen.queryByText('Assertion Type Distribution')).not.toBeInTheDocument();
    });

    it('should count assertion types correctly', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          assertions={mockAssertions}
        />
      );

      // immediate: 2, concurrent: 2
      expect(screen.getByText('Immediate')).toBeInTheDocument();
      expect(screen.getByText('Concurrent')).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('should show overview tab by default', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      expect(screen.getByText('Specifications')).toBeInTheDocument();
      expect(screen.queryByTestId('traceability-matrix')).not.toBeInTheDocument();
    });

    it('should switch to traceability matrix tab', async () => {
      const user = userEvent.setup();
      
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      const traceabilityTab = screen.getByText('Traceability Matrix');
      await user.click(traceabilityTab);

      await waitFor(() => {
        expect(screen.getByTestId('traceability-matrix')).toBeInTheDocument();
      });
    });

    it('should switch to signal dependencies tab', async () => {
      const user = userEvent.setup();
      
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      const dependenciesTab = screen.getByText('Signal Dependencies');
      await user.click(dependenciesTab);

      await waitFor(() => {
        expect(screen.getByTestId('signal-dependency-graph')).toBeInTheDocument();
      });
    });

    it('should pass correct projectId to child components', async () => {
      const user = userEvent.setup();
      
      render(
        <Dashboard
          projectId="test-123"
          projectName="Test Project"
          statistics={mockStatistics}
        />
      );

      const traceabilityTab = screen.getByText('Traceability Matrix');
      await user.click(traceabilityTab);

      await waitFor(() => {
        expect(screen.getByText(/test-123/)).toBeInTheDocument();
      });
    });
  });

  describe('Statistics Accuracy', () => {
    it('should calculate coverage percentage correctly', () => {
      const stats = {
        total_specs: 1,
        total_rtl_files: 1,
        total_assertions: 10,
        total_requirements: 50,
        covered_requirements: 25,
        coverage_percentage: 50
      };

      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={stats}
        />
      );

      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should handle partial coverage', () => {
      const stats = {
        total_specs: 1,
        total_rtl_files: 1,
        total_assertions: 10,
        total_requirements: 3,
        covered_requirements: 1,
        coverage_percentage: 33.33
      };

      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={stats}
        />
      );

      expect(screen.getByText('33%')).toBeInTheDocument();
    });

    it('should handle 100% coverage', () => {
      const stats = {
        total_specs: 1,
        total_rtl_files: 1,
        total_assertions: 10,
        total_requirements: 10,
        covered_requirements: 10,
        coverage_percentage: 100
      };

      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={stats}
        />
      );

      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty assertions array', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          assertions={[]}
        />
      );

      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });

    it('should handle missing optional statistics', () => {
      const minimalStats = {
        total_specs: 0,
        total_rtl_files: 0,
        total_assertions: 0
      };

      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={minimalStats}
        />
      );

      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('0 of 0 requirements')).toBeInTheDocument();
    });

    it('should handle empty coverage by category', () => {
      render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mockStatistics}
          coverageByCategory={{}}
        />
      );

      expect(screen.queryByText('Coverage by Requirement Category')).not.toBeInTheDocument();
    });
  });

  describe('Visual Indicators', () => {
    it('should use green color for high coverage', () => {
      const highCoverageStats = {
        ...mockStatistics,
        coverage_percentage: 85
      };

      const { container } = render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={highCoverageStats}
        />
      );

      // Check for green background class
      const coverageCard = container.querySelector('.bg-green-100');
      expect(coverageCard).toBeInTheDocument();
    });

    it('should use yellow color for medium coverage', () => {
      const mediumCoverageStats = {
        ...mockStatistics,
        coverage_percentage: 65
      };

      const { container } = render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={mediumCoverageStats}
        />
      );

      // Check for yellow background class
      const coverageCard = container.querySelector('.bg-yellow-100');
      expect(coverageCard).toBeInTheDocument();
    });

    it('should use red color for low coverage', () => {
      const lowCoverageStats = {
        ...mockStatistics,
        coverage_percentage: 45
      };

      const { container } = render(
        <Dashboard
          projectId="test-project"
          projectName="Test Project"
          statistics={lowCoverageStats}
        />
      );

      // Check for red background class
      const coverageCard = container.querySelector('.bg-red-100');
      expect(coverageCard).toBeInTheDocument();
    });
  });
});

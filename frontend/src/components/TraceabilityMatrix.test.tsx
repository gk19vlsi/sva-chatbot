/**
 * TraceabilityMatrix Component Tests
 * 
 * Tests matrix rendering, filtering, and navigation.
 * 
 * Validates Requirements 8.5
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TraceabilityMatrix from './TraceabilityMatrix';

// Mock fetch
global.fetch = vi.fn();

describe('TraceabilityMatrix Component', () => {
  const mockMatrix = [
    {
      requirement: {
        id: 'req-1',
        text: 'The system shall validate input data',
        category: 'functional'
      },
      assertions: [
        {
          id: 'assert-1',
          code: 'assert property...',
          confidence_score: 0.9,
          quality_score: 0.85
        }
      ],
      coverage: true
    },
    {
      requirement: {
        id: 'req-2',
        text: 'The system shall respond within 100ms',
        category: 'timing'
      },
      assertions: [
        {
          id: 'assert-2',
          code: 'assert property...',
          confidence_score: 0.8,
          quality_score: 0.75
        },
        {
          id: 'assert-3',
          code: 'assert property...',
          confidence_score: 0.85,
          quality_score: 0.8
        }
      ],
      coverage: true
    },
    {
      requirement: {
        id: 'req-3',
        text: 'The system shall handle errors gracefully',
        category: 'safety'
      },
      assertions: [],
      coverage: false
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('token', 'test-token');
    
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ matrix: mockMatrix })
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Initial Rendering', () => {
    it('should show loading state initially', () => {
      render(<TraceabilityMatrix projectId="test-project" />);
      
      expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument();
    });

    it('should fetch matrix data on mount', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/projects/test-project/traceability-matrix'),
          expect.objectContaining({
            headers: {
              'Authorization': 'Bearer test-token'
            }
          })
        );
      });
    });

    it('should display matrix after loading', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('Traceability Matrix')).toBeInTheDocument();
      });
    });
  });

  describe('Statistics Display', () => {
    it('should display total requirements count', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument();
        expect(screen.getByText('Total Requirements')).toBeInTheDocument();
      });
    });

    it('should display covered requirements count', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('Covered')).toBeInTheDocument();
      });
    });

    it('should calculate coverage percentage correctly', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('66.7%')).toBeInTheDocument();
      });
    });

    it('should handle 100% coverage', async () => {
      const fullCoverageMatrix = mockMatrix.map(entry => ({
        ...entry,
        coverage: true,
        assertions: entry.assertions.length > 0 ? entry.assertions : [
          { id: 'new-assert', code: 'assert...', confidence_score: 0.9 }
        ]
      }));

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ matrix: fullCoverageMatrix })
      });

      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('100.0%')).toBeInTheDocument();
      });
    });

    it('should handle zero coverage', async () => {
      const noCoverageMatrix = mockMatrix.map(entry => ({
        ...entry,
        coverage: false,
        assertions: []
      }));

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ matrix: noCoverageMatrix })
      });

      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('0.0%')).toBeInTheDocument();
      });
    });
  });

  describe('Matrix Table', () => {
    it('should display all requirements', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/validate input data/)).toBeInTheDocument();
        expect(screen.getByText(/respond within 100ms/)).toBeInTheDocument();
        expect(screen.getByText(/handle errors gracefully/)).toBeInTheDocument();
      });
    });

    it('should display requirement categories', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('functional')).toBeInTheDocument();
        expect(screen.getByText('timing')).toBeInTheDocument();
        expect(screen.getByText('safety')).toBeInTheDocument();
      });
    });

    it('should display assertion counts', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('Assertion 1')).toBeInTheDocument();
        expect(screen.getByText('Assertion 2')).toBeInTheDocument();
      });
    });

    it('should show "No assertions" for uncovered requirements', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('No assertions')).toBeInTheDocument();
      });
    });

    it('should display coverage status badges', async () => {
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        const coveredBadges = screen.getAllByText('Covered');
        const uncoveredBadges = screen.getAllByText('Uncovered');
        expect(coveredBadges.length).toBeGreaterThan(0);
        expect(uncoveredBadges.length).toBeGreaterThan(0);
      });
    });

    it('should truncate long requirement text', async () => {
      const longTextMatrix = [{
        requirement: {
          id: 'req-long',
          text: 'A'.repeat(150),
          category: 'functional'
        },
        assertions: [],
        coverage: false
      }];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ matrix: longTextMatrix })
      });

      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        const text = screen.getByText(/A{100}\.\.\./, { exact: false });
        expect(text).toBeInTheDocument();
      });
    });
  });

  describe('Filtering', () => {
    it('should filter by category', async () => {
      const user = userEvent.setup();
      
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/validate input data/)).toBeInTheDocument();
      });

      const categorySelect = screen.getByLabelText('Category');
      await user.selectOptions(categorySelect, 'functional');

      await waitFor(() => {
        expect(screen.getByText(/validate input data/)).toBeInTheDocument();
        expect(screen.queryByText(/respond within 100ms/)).not.toBeInTheDocument();
      });
    });

    it('should filter by coverage status', async () => {
      const user = userEvent.setup();
      
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/validate input data/)).toBeInTheDocument();
      });

      const coverageSelect = screen.getByLabelText('Coverage');
      await user.selectOptions(coverageSelect, 'uncovered');

      await waitFor(() => {
        expect(screen.queryByText(/validate input data/)).not.toBeInTheDocument();
        expect(screen.getByText(/handle errors gracefully/)).toBeInTheDocument();
      });
    });

    it('should show all requirements when filter is "all"', async () => {
      const user = userEvent.setup();
      
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/validate input data/)).toBeInTheDocument();
      });

      const categorySelect = screen.getByLabelText('Category');
      await user.selectOptions(categorySelect, 'functional');
      await user.selectOptions(categorySelect, 'all');

      await waitFor(() => {
        expect(screen.getByText(/validate input data/)).toBeInTheDocument();
        expect(screen.getByText(/respond within 100ms/)).toBeInTheDocument();
      });
    });

    it('should show message when no requirements match filters', async () => {
      const user = userEvent.setup();
      
      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/validate input data/)).toBeInTheDocument();
      });

      const categorySelect = screen.getByLabelText('Category');
      await user.selectOptions(categorySelect, 'functional');
      
      const coverageSelect = screen.getByLabelText('Coverage');
      await user.selectOptions(coverageSelect, 'uncovered');

      await waitFor(() => {
        expect(screen.getByText(/No requirements found matching/)).toBeInTheDocument();
      });
    });
  });

  describe('Click Handlers', () => {
    it('should call onRequirementClick when requirement is clicked', async () => {
      const user = userEvent.setup();
      const onRequirementClick = vi.fn();
      
      render(
        <TraceabilityMatrix
          projectId="test-project"
          onRequirementClick={onRequirementClick}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/validate input data/)).toBeInTheDocument();
      });

      const requirementButton = screen.getByText(/validate input data/);
      await user.click(requirementButton);

      expect(onRequirementClick).toHaveBeenCalledWith('req-1');
    });

    it('should call onAssertionClick when assertion is clicked', async () => {
      const user = userEvent.setup();
      const onAssertionClick = vi.fn();
      
      render(
        <TraceabilityMatrix
          projectId="test-project"
          onAssertionClick={onAssertionClick}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Assertion 1')).toBeInTheDocument();
      });

      const assertionButton = screen.getByText('Assertion 1');
      await user.click(assertionButton);

      expect(onAssertionClick).toHaveBeenCalledWith('assert-1');
    });
  });

  describe('Error Handling', () => {
    it('should display error message on fetch failure', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/Error: Network error/)).toBeInTheDocument();
      });
    });

    it('should display error message on non-ok response', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 404
      });

      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to fetch traceability matrix/)).toBeInTheDocument();
      });
    });

    it('should allow retry after error', async () => {
      const user = userEvent.setup();
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/Error: Network error/)).toBeInTheDocument();
      });

      // Mock successful response for retry
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ matrix: mockMatrix })
      });

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Traceability Matrix')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('should handle empty matrix', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ matrix: [] })
      });

      render(<TraceabilityMatrix projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument();
        expect(screen.getByText('0.0%')).toBeInTheDocument();
      });
    });
  });
});

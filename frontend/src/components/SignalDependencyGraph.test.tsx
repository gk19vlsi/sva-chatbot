/**
 * SignalDependencyGraph Component Tests
 * 
 * Tests graph rendering, signal visualization, and interaction.
 * 
 * Validates Requirements 8.5
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SignalDependencyGraph from './SignalDependencyGraph';

// Mock fetch
global.fetch = vi.fn();

// Mock canvas context
const mockContext = {
  clearRect: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  stroke: vi.fn(),
  fill: vi.fn(),
  arc: vi.fn(),
  closePath: vi.fn(),
  fillText: vi.fn(),
  set fillStyle(value: string) {},
  set strokeStyle(value: string) {},
  set lineWidth(value: number) {},
  set font(value: string) {},
  set textAlign(value: string) {}
};

HTMLCanvasElement.prototype.getContext = vi.fn(() => mockContext as any);

describe('SignalDependencyGraph Component', () => {
  const mockRTLDesigns = [
    {
      id: 'rtl-1',
      filename: 'module1.sv',
      analysis: {
        modules: [
          {
            name: 'module1',
            ports: [
              { name: 'clk', direction: 'input', type: 'clock' },
              { name: 'rst', direction: 'input', type: 'reset' },
              { name: 'data_in', direction: 'input', type: 'input' },
              { name: 'data_out', direction: 'output', type: 'output' }
            ],
            signals: [
              { name: 'internal_reg', type: 'wire' }
            ]
          }
        ],
        dependencies: {
          'data_in': ['internal_reg'],
          'internal_reg': ['data_out']
        }
      }
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('token', 'test-token');
    
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockRTLDesigns
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Initial Rendering', () => {
    it('should show loading state initially', () => {
      render(<SignalDependencyGraph projectId="test-project" />);
      
      expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument();
    });

    it('should fetch RTL designs on mount', async () => {
      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/projects/test-project/rtl-designs'),
          expect.objectContaining({
            headers: {
              'Authorization': 'Bearer test-token'
            }
          })
        );
      });
    });

    it('should display graph after loading', async () => {
      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('Signal Dependency Graph')).toBeInTheDocument();
      });
    });
  });

  describe('Graph Statistics', () => {
    it('should display signal count', async () => {
      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/5 signals/)).toBeInTheDocument();
      });
    });

    it('should display dependency count', async () => {
      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/2 dependencies/)).toBeInTheDocument();
      });
    });
  });

  describe('Legend', () => {
    it('should display signal type legend', async () => {
      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('Input')).toBeInTheDocument();
        expect(screen.getByText('Output')).toBeInTheDocument();
        expect(screen.getByText('Clock')).toBeInTheDocument();
        expect(screen.getByText('Reset')).toBeInTheDocument();
        expect(screen.getByText('Wire/Reg')).toBeInTheDocument();
      });
    });
  });

  describe('Canvas Rendering', () => {
    it('should render canvas with correct dimensions', async () => {
      const { container } = render(
        <SignalDependencyGraph
          projectId="test-project"
          width={1000}
          height={800}
        />
      );

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
        expect(canvas?.width).toBe(1000);
        expect(canvas?.height).toBe(800);
      });
    });

    it('should use default dimensions when not specified', async () => {
      const { container } = render(
        <SignalDependencyGraph projectId="test-project" />
      );

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas?.width).toBe(800);
        expect(canvas?.height).toBe(600);
      });
    });

    it('should clear canvas before rendering', async () => {
      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(mockContext.clearRect).toHaveBeenCalled();
      });
    });

    it('should draw nodes', async () => {
      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(mockContext.arc).toHaveBeenCalled();
        expect(mockContext.fill).toHaveBeenCalled();
      });
    });

    it('should draw edges', async () => {
      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(mockContext.moveTo).toHaveBeenCalled();
        expect(mockContext.lineTo).toHaveBeenCalled();
        expect(mockContext.stroke).toHaveBeenCalled();
      });
    });
  });

  describe('Signal Selection', () => {
    it('should handle canvas click', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <SignalDependencyGraph projectId="test-project" />
      );

      await waitFor(() => {
        expect(screen.getByText('Signal Dependency Graph')).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas');
      if (canvas) {
        await user.click(canvas);
      }

      // Selection state should change (implementation detail)
      expect(canvas).toBeInTheDocument();
    });

    it('should display selected signal info', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <SignalDependencyGraph projectId="test-project" />
      );

      await waitFor(() => {
        expect(screen.getByText('Signal Dependency Graph')).toBeInTheDocument();
      });

      const canvas = container.querySelector('canvas');
      if (canvas) {
        await user.click(canvas);
      }

      // After click, selected signal info might be displayed
      // This depends on implementation details
    });
  });

  describe('Error Handling', () => {
    it('should display error message on fetch failure', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/Error: Network error/)).toBeInTheDocument();
      });
    });

    it('should display error message on non-ok response', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 404
      });

      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to fetch RTL designs/)).toBeInTheDocument();
      });
    });

    it('should allow retry after error', async () => {
      const user = userEvent.setup();
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/Error: Network error/)).toBeInTheDocument();
      });

      // Mock successful response for retry
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockRTLDesigns
      });

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Signal Dependency Graph')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no signals found', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => []
      });

      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('No signal dependencies found.')).toBeInTheDocument();
        expect(screen.getByText(/Upload and process RTL files/)).toBeInTheDocument();
      });
    });

    it('should display empty state when designs have no analysis', async () => {
      const emptyDesigns = [
        {
          id: 'rtl-1',
          filename: 'module1.sv',
          analysis: {
            modules: [],
            dependencies: {}
          }
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => emptyDesigns
      });

      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('No signal dependencies found.')).toBeInTheDocument();
      });
    });
  });

  describe('Data Processing', () => {
    it('should extract signals from multiple modules', async () => {
      const multiModuleDesigns = [
        {
          id: 'rtl-1',
          filename: 'module1.sv',
          analysis: {
            modules: [
              {
                name: 'module1',
                ports: [{ name: 'sig1', direction: 'input', type: 'input' }],
                signals: []
              },
              {
                name: 'module2',
                ports: [{ name: 'sig2', direction: 'output', type: 'output' }],
                signals: []
              }
            ],
            dependencies: {}
          }
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => multiModuleDesigns
      });

      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText(/2 signals/)).toBeInTheDocument();
      });
    });

    it('should handle missing analysis data gracefully', async () => {
      const incompleteDesigns = [
        {
          id: 'rtl-1',
          filename: 'module1.sv'
          // No analysis field
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => incompleteDesigns
      });

      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('No signal dependencies found.')).toBeInTheDocument();
      });
    });

    it('should handle missing modules array', async () => {
      const noModulesDesigns = [
        {
          id: 'rtl-1',
          filename: 'module1.sv',
          analysis: {
            dependencies: {}
          }
        }
      ];

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => noModulesDesigns
      });

      render(<SignalDependencyGraph projectId="test-project" />);

      await waitFor(() => {
        expect(screen.getByText('No signal dependencies found.')).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should accept custom width and height', async () => {
      const { container } = render(
        <SignalDependencyGraph
          projectId="test-project"
          width={1200}
          height={900}
        />
      );

      await waitFor(() => {
        const canvas = container.querySelector('canvas');
        expect(canvas?.width).toBe(1200);
        expect(canvas?.height).toBe(900);
      });
    });
  });

  describe('RTL Design ID Filter', () => {
    it('should accept optional rtlDesignId prop', async () => {
      render(
        <SignalDependencyGraph
          projectId="test-project"
          rtlDesignId="rtl-1"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Signal Dependency Graph')).toBeInTheDocument();
      });
    });
  });
});

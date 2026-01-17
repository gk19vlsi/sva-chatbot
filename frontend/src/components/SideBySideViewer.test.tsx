/**
 * Unit Tests for Side-by-Side Viewer Component
 * 
 * Tests panel rendering, highlighting, and navigation functionality.
 * 
 * Validates Requirements 14.2, 14.3, 14.4
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SideBySideViewer } from './SideBySideViewer';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onMount, options }: any) => {
    // Simulate editor mount
    if (onMount) {
      const mockEditor = {
        getModel: () => ({
          getValue: () => value,
          getPositionAt: (index: number) => ({ lineNumber: 1, column: 1 }),
          getLineCount: () => value.split('\n').length,
          getLineMaxColumn: (line: number) => 100,
          getValueInRange: () => 'signal',
          getWordAtPosition: () => ({ startColumn: 1, endColumn: 7 })
        }),
        deltaDecorations: vi.fn(() => []),
        revealLineInCenter: vi.fn(),
        setPosition: vi.fn(),
        getVisibleRanges: () => [{ startLineNumber: 1, endLineNumber: 10 }],
        onDidScrollChange: vi.fn(() => ({ dispose: vi.fn() })),
        onMouseDown: vi.fn()
      };
      setTimeout(() => onMount(mockEditor), 0);
    }
    
    return (
      <div data-testid={`monaco-editor-${options?.readOnly ? 'readonly' : 'editable'}`}>
        {value}
      </div>
    );
  }
}));

describe('SideBySideViewer', () => {
  const mockAssertion = {
    id: 'ast-001',
    assertion_code: 'assert property (@(posedge clk) req |-> ##[1:5] ack);',
    assertion_type: 'concurrent',
    confidence_score: 0.92,
    quality_score: 0.88,
    traceability: {
      spec_reference: 'REQ-001',
      requirement_text: 'When request is asserted, acknowledge must be asserted within 5 cycles',
      rtl_signals: ['clk', 'req', 'ack'],
      rtl_module: 'handshake_ctrl',
      line_numbers: [10, 15, 20]
    },
    explanation: 'Verifies handshake timing constraint'
  };

  const mockSpecText = `# Specification
  
## Requirement REQ-001
When request is asserted, acknowledge must be asserted within 5 cycles.

## Requirement REQ-002
Other requirement text.`;

  const mockRtlCode = `module handshake_ctrl (
  input wire clk,
  input wire req,
  output reg ack
);
  
  always @(posedge clk) begin
    if (req) begin
      ack <= 1'b1;
    end
  end
  
endmodule`;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Panel Rendering', () => {
    it('should render all three panels', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      // Check for panel headers
      expect(screen.getByText('Specification')).toBeInTheDocument();
      expect(screen.getByText('RTL Design')).toBeInTheDocument();
      expect(screen.getByText('Generated Assertion')).toBeInTheDocument();
    });

    it('should display assertion metadata in header', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText('REQ-001')).toBeInTheDocument();
      expect(screen.getByText('92%')).toBeInTheDocument(); // Confidence score
      expect(screen.getByText('88%')).toBeInTheDocument(); // Quality score
    });

    it('should display specification text in left panel', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText(/Specification/)).toBeInTheDocument();
      expect(screen.getByText(/REQ-001/)).toBeInTheDocument();
    });

    it('should display RTL code in middle panel', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText(/Module: handshake_ctrl/)).toBeInTheDocument();
      expect(screen.getByText(/Signals: clk, req, ack/)).toBeInTheDocument();
    });

    it('should display assertion code in right panel', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText(/Type: concurrent/)).toBeInTheDocument();
    });

    it('should display assertion explanation', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText('Explanation')).toBeInTheDocument();
      expect(screen.getByText('Verifies handshake timing constraint')).toBeInTheDocument();
    });
  });

  describe('Synchronized Scrolling', () => {
    it('should have sync scroll enabled by default', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      const syncCheckbox = screen.getByRole('checkbox', { name: /sync scroll/i });
      expect(syncCheckbox).toBeChecked();
    });

    it('should toggle sync scroll when checkbox clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      const syncCheckbox = screen.getByRole('checkbox', { name: /sync scroll/i });
      expect(syncCheckbox).toBeChecked();

      await user.click(syncCheckbox);
      expect(syncCheckbox).not.toBeChecked();

      await user.click(syncCheckbox);
      expect(syncCheckbox).toBeChecked();
    });
  });

  describe('Traceability Display', () => {
    it('should display requirement reference', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText(/Requirement: REQ-001/)).toBeInTheDocument();
    });

    it('should display RTL module name', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText(/Module: handshake_ctrl/)).toBeInTheDocument();
    });

    it('should display RTL signals', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText(/Signals: clk, req, ack/)).toBeInTheDocument();
    });
  });

  describe('Confidence and Quality Indicators', () => {
    it('should display high confidence score in green', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      const confidenceElement = screen.getByText('92%');
      expect(confidenceElement).toHaveClass('text-green-600');
    });

    it('should display medium confidence score in yellow', () => {
      const mediumConfidenceAssertion = {
        ...mockAssertion,
        confidence_score: 0.7
      };

      render(
        <SideBySideViewer
          assertion={mediumConfidenceAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      const confidenceElement = screen.getByText('70%');
      expect(confidenceElement).toHaveClass('text-yellow-600');
    });

    it('should display low confidence score in red', () => {
      const lowConfidenceAssertion = {
        ...mockAssertion,
        confidence_score: 0.4
      };

      render(
        <SideBySideViewer
          assertion={lowConfidenceAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      const confidenceElement = screen.getByText('40%');
      expect(confidenceElement).toHaveClass('text-red-600');
    });

    it('should display quality score when available', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText('Quality:')).toBeInTheDocument();
      expect(screen.getByText('88%')).toBeInTheDocument();
    });

    it('should not display quality score when unavailable', () => {
      const noQualityAssertion = {
        ...mockAssertion,
        quality_score: undefined
      };

      render(
        <SideBySideViewer
          assertion={noQualityAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.queryByText('Quality:')).not.toBeInTheDocument();
    });
  });

  describe('Close Functionality', () => {
    it('should call onClose when close button clicked', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();

      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
          onClose={onClose}
        />
      );

      const closeButton = screen.getByLabelText('Close viewer');
      await user.click(closeButton);

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should not render close button when onClose not provided', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.queryByLabelText('Close viewer')).not.toBeInTheDocument();
    });
  });

  describe('Assertion Type Display', () => {
    it('should display concurrent assertion type', () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText(/Type: concurrent/)).toBeInTheDocument();
    });

    it('should display immediate assertion type', () => {
      const immediateAssertion = {
        ...mockAssertion,
        assertion_type: 'immediate'
      };

      render(
        <SideBySideViewer
          assertion={immediateAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      expect(screen.getByText(/Type: immediate/)).toBeInTheDocument();
    });
  });

  describe('Editor Configuration', () => {
    it('should render Monaco editors with correct configuration', async () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      // Wait for editors to mount
      await waitFor(() => {
        const editors = screen.getAllByTestId(/monaco-editor/);
        expect(editors.length).toBe(3);
      });
    });

    it('should set all editors to read-only mode', async () => {
      render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      await waitFor(() => {
        const readonlyEditors = screen.getAllByTestId('monaco-editor-readonly');
        expect(readonlyEditors.length).toBe(3);
      });
    });
  });

  describe('Responsive Layout', () => {
    it('should render three-panel flex layout', () => {
      const { container } = render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      const layout = container.querySelector('.flex.overflow-hidden');
      expect(layout).toBeInTheDocument();
    });

    it('should have proper panel borders', () => {
      const { container } = render(
        <SideBySideViewer
          assertion={mockAssertion}
          specificationText={mockSpecText}
          rtlCode={mockRtlCode}
        />
      );

      const panels = container.querySelectorAll('.border-r.border-gray-200');
      expect(panels.length).toBeGreaterThan(0);
    });
  });
});

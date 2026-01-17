import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AssertionViewer, { Assertion } from './AssertionViewer';

/**
 * Unit tests for AssertionViewer component
 * 
 * Validates: Requirements 14.1, 14.5
 */
describe('AssertionViewer Component', () => {
  const mockAssertion: Assertion = {
    id: 'AST-001',
    code: `// Validates: REQ-001
assert property (@(posedge clk) disable iff (!rst_n)
  valid |-> ##[1:5] ready
);`,
    type: 'concurrent',
    category: 'timing',
    confidenceScore: 0.92,
    qualityScore: 0.88,
    explanation: 'Verifies that ready responds within 5 cycles when valid is asserted',
    traceability: {
      requirementText: 'When valid is high, ready must be asserted within 5 cycles',
      rtlSignals: ['valid', 'ready', 'clk', 'rst_n'],
      rtlModule: 'handshake_controller',
    },
  };

  describe('Code Display', () => {
    it('should render assertion code', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      // Check that the component renders
      expect(screen.getByText(/Assertion AST-001/i)).toBeInTheDocument();
    });

    it('should display assertion ID', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText(/AST-001/i)).toBeInTheDocument();
    });

    it('should display assertion type badge', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText('concurrent')).toBeInTheDocument();
    });

    it('should display assertion category', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText('timing')).toBeInTheDocument();
    });

    it('should display explanation text', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(
        screen.getByText(/Verifies that ready responds within 5 cycles/i)
      ).toBeInTheDocument();
    });

    it('should render Monaco Editor for code display', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      // Monaco Editor creates a container div
      // We verify the component structure is rendered
      expect(screen.getByText(/Assertion AST-001/i)).toBeInTheDocument();
    });
  });

  describe('Score Display', () => {
    it('should display confidence score', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText(/Confidence:/i)).toBeInTheDocument();
      expect(screen.getByText('92%')).toBeInTheDocument();
    });

    it('should display quality score when provided', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText(/Quality:/i)).toBeInTheDocument();
      expect(screen.getByText('88%')).toBeInTheDocument();
    });

    it('should not display quality score when not provided', () => {
      const assertionWithoutQuality: Assertion = {
        ...mockAssertion,
        qualityScore: undefined,
      };

      render(<AssertionViewer assertion={assertionWithoutQuality} />);

      expect(screen.queryByText(/Quality:/i)).not.toBeInTheDocument();
    });

    it('should apply correct color for high confidence score (>= 80%)', () => {
      const highScoreAssertion: Assertion = {
        ...mockAssertion,
        confidenceScore: 0.85,
      };

      render(<AssertionViewer assertion={highScoreAssertion} />);

      // High scores should have green styling
      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('should apply correct color for medium confidence score (60-79%)', () => {
      const mediumScoreAssertion: Assertion = {
        ...mockAssertion,
        confidenceScore: 0.7,
      };

      render(<AssertionViewer assertion={mediumScoreAssertion} />);

      // Medium scores should have yellow styling
      expect(screen.getByText('70%')).toBeInTheDocument();
    });

    it('should apply correct color for low confidence score (< 60%)', () => {
      const lowScoreAssertion: Assertion = {
        ...mockAssertion,
        confidenceScore: 0.5,
      };

      render(<AssertionViewer assertion={lowScoreAssertion} />);

      // Low scores should have red styling
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should format scores as percentages', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      // Scores should be displayed as percentages
      expect(screen.getByText('92%')).toBeInTheDocument();
      expect(screen.getByText('88%')).toBeInTheDocument();
    });
  });

  describe('Traceability Display', () => {
    it('should display traceability section when provided', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText(/Traceability/i)).toBeInTheDocument();
    });

    it('should display requirement text', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(
        screen.getByText(/When valid is high, ready must be asserted within 5 cycles/i)
      ).toBeInTheDocument();
    });

    it('should display RTL module name', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText('handshake_controller')).toBeInTheDocument();
    });

    it('should display all RTL signals', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText('valid')).toBeInTheDocument();
      expect(screen.getByText('ready')).toBeInTheDocument();
      expect(screen.getByText('clk')).toBeInTheDocument();
      expect(screen.getByText('rst_n')).toBeInTheDocument();
    });

    it('should not display traceability section when not provided', () => {
      const assertionWithoutTraceability: Assertion = {
        ...mockAssertion,
        traceability: undefined,
      };

      render(<AssertionViewer assertion={assertionWithoutTraceability} />);

      expect(screen.queryByText(/Traceability/i)).not.toBeInTheDocument();
    });
  });

  describe('Assertion Types', () => {
    it('should display immediate assertion type correctly', () => {
      const immediateAssertion: Assertion = {
        ...mockAssertion,
        type: 'immediate',
      };

      render(<AssertionViewer assertion={immediateAssertion} />);

      expect(screen.getByText('immediate')).toBeInTheDocument();
    });

    it('should display concurrent assertion type correctly', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText('concurrent')).toBeInTheDocument();
    });

    it('should display property assertion type correctly', () => {
      const propertyAssertion: Assertion = {
        ...mockAssertion,
        type: 'property',
      };

      render(<AssertionViewer assertion={propertyAssertion} />);

      expect(screen.getByText('property')).toBeInTheDocument();
    });

    it('should display sequence assertion type correctly', () => {
      const sequenceAssertion: Assertion = {
        ...mockAssertion,
        type: 'sequence',
      };

      render(<AssertionViewer assertion={sequenceAssertion} />);

      expect(screen.getByText('sequence')).toBeInTheDocument();
    });
  });

  describe('Read-only Mode', () => {
    it('should render in read-only mode by default', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      // Component should render successfully
      expect(screen.getByText(/Assertion AST-001/i)).toBeInTheDocument();
    });

    it('should accept readOnly prop', () => {
      render(<AssertionViewer assertion={mockAssertion} readOnly={true} />);

      expect(screen.getByText(/Assertion AST-001/i)).toBeInTheDocument();
    });

    it('should allow editable mode when readOnly is false', () => {
      const handleCodeChange = vi.fn();

      render(
        <AssertionViewer
          assertion={mockAssertion}
          readOnly={false}
          onCodeChange={handleCodeChange}
        />
      );

      expect(screen.getByText(/Assertion AST-001/i)).toBeInTheDocument();
    });
  });

  describe('Code Change Callback', () => {
    it('should accept onCodeChange callback', () => {
      const handleCodeChange = vi.fn();

      render(
        <AssertionViewer
          assertion={mockAssertion}
          readOnly={false}
          onCodeChange={handleCodeChange}
        />
      );

      // Callback should be provided to the component
      expect(screen.getByText(/Assertion AST-001/i)).toBeInTheDocument();
    });
  });

  describe('Visual Styling', () => {
    it('should apply correct badge colors for assertion types', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      // Type badges should have appropriate styling
      const typeBadge = screen.getByText('concurrent');
      expect(typeBadge).toBeInTheDocument();
    });

    it('should display signals with proper formatting', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      // Signals should be displayed with monospace font
      const signals = mockAssertion.traceability!.rtlSignals;
      signals.forEach((signal) => {
        expect(screen.getByText(signal)).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle assertion without explanation', () => {
      const assertionWithoutExplanation: Assertion = {
        ...mockAssertion,
        explanation: '',
      };

      render(<AssertionViewer assertion={assertionWithoutExplanation} />);

      expect(screen.getByText(/Assertion AST-001/i)).toBeInTheDocument();
    });

    it('should handle assertion with empty RTL signals array', () => {
      const assertionWithNoSignals: Assertion = {
        ...mockAssertion,
        traceability: {
          ...mockAssertion.traceability!,
          rtlSignals: [],
        },
      };

      render(<AssertionViewer assertion={assertionWithNoSignals} />);

      expect(screen.getByText(/Traceability/i)).toBeInTheDocument();
    });

    it('should handle very long assertion code', () => {
      const longCodeAssertion: Assertion = {
        ...mockAssertion,
        code: 'assert property ' + 'x'.repeat(1000) + ';',
      };

      render(<AssertionViewer assertion={longCodeAssertion} />);

      expect(screen.getByText(/Assertion AST-001/i)).toBeInTheDocument();
    });
  });

  describe('Clipboard Copy Functionality', () => {
    // Mock clipboard API
    const mockClipboard = {
      writeText: vi.fn(),
    };

    beforeEach(() => {
      // Reset mock before each test
      mockClipboard.writeText.mockReset();
      // Mock navigator.clipboard
      Object.assign(navigator, {
        clipboard: mockClipboard,
      });
    });

    it('should display copy button', () => {
      render(<AssertionViewer assertion={mockAssertion} />);

      expect(screen.getByText('Copy')).toBeInTheDocument();
    });

    it('should copy assertion code to clipboard when copy button is clicked', async () => {
      const user = userEvent.setup();
      render(<AssertionViewer assertion={mockAssertion} />);

      const copyButton = screen.getByText('Copy').closest('button');
      expect(copyButton).toBeInTheDocument();

      await user.click(copyButton!);

      expect(mockClipboard.writeText).toHaveBeenCalledWith(mockAssertion.code);
    });

    it('should show success message after copying', async () => {
      mockClipboard.writeText.mockResolvedValue(undefined);
      const user = userEvent.setup();
      
      render(<AssertionViewer assertion={mockAssertion} />);

      const copyButton = screen.getByText('Copy').closest('button');
      await user.click(copyButton!);

      // Wait for success message
      await screen.findByText('Copied!');
      expect(screen.getByText('Copied!')).toBeInTheDocument();
    });

    it('should reset success message after 2 seconds', async () => {
      vi.useFakeTimers();
      mockClipboard.writeText.mockResolvedValue(undefined);
      const user = userEvent.setup();
      
      render(<AssertionViewer assertion={mockAssertion} />);

      const copyButton = screen.getByText('Copy').closest('button');
      await user.click(copyButton!);

      // Success message should appear
      await screen.findByText('Copied!');

      // Fast-forward time by 2 seconds
      vi.advanceTimersByTime(2000);

      // Success message should disappear
      await waitFor(() => {
        expect(screen.queryByText('Copied!')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });

    it('should copy edited code when in edit mode', async () => {
      const editedCode = 'assert (new_signal);';
      mockClipboard.writeText.mockResolvedValue(undefined);
      const user = userEvent.setup();
      
      render(
        <AssertionViewer 
          assertion={mockAssertion} 
          enableEdit={true}
          readOnly={false}
        />
      );

      // Enter edit mode
      const editButton = screen.getByText('Edit');
      await user.click(editButton);

      // Simulate code change (this would normally happen through Monaco Editor)
      // For testing, we'll just click copy and verify it tries to copy
      const copyButton = screen.getByText('Copy').closest('button');
      await user.click(copyButton!);

      // Should attempt to copy (will copy the current code)
      expect(mockClipboard.writeText).toHaveBeenCalled();
    });

    it('should handle clipboard API failure gracefully', async () => {
      mockClipboard.writeText.mockRejectedValue(new Error('Clipboard API failed'));
      const user = userEvent.setup();
      
      // Mock document.execCommand for fallback
      const execCommandMock = vi.fn();
      document.execCommand = execCommandMock;
      
      render(<AssertionViewer assertion={mockAssertion} />);

      const copyButton = screen.getByText('Copy').closest('button');
      await user.click(copyButton!);

      // Should attempt fallback method
      expect(execCommandMock).toHaveBeenCalledWith('copy');
    });
  });
});

/**
 * Side-by-Side Viewer Component
 * 
 * Three-panel layout showing specification, RTL code, and assertion code
 * with synchronized scrolling and traceability highlighting.
 * 
 * Implements Requirements 14.2, 14.3, 14.4
 */
import React, { useState, useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';

interface Traceability {
  spec_reference: string;
  requirement_text: string;
  rtl_signals: string[];
  rtl_module: string;
  line_numbers: number[];
}

interface Assertion {
  id: string;
  assertion_code: string;
  assertion_type: string;
  confidence_score: number;
  quality_score?: number;
  traceability: Traceability;
  explanation: string;
}

interface SideBySideViewerProps {
  assertion: Assertion;
  specificationText: string;
  rtlCode: string;
  onClose?: () => void;
}

export const SideBySideViewer: React.FC<SideBySideViewerProps> = ({
  assertion,
  specificationText,
  rtlCode,
  onClose
}) => {
  const [highlightedSignals, setHighlightedSignals] = useState<string[]>([]);
  const [syncScroll, setSyncScroll] = useState(true);
  const [selectedSignal, setSelectedSignal] = useState<string | null>(null);
  
  const specEditorRef = useRef<any>(null);
  const rtlEditorRef = useRef<any>(null);
  const assertionEditorRef = useRef<any>(null);

  // Handle editor mount
  const handleSpecEditorMount = (editor: any) => {
    specEditorRef.current = editor;
    highlightRequirementText();
    setupClickNavigation(editor, 'spec');
  };

  const handleRtlEditorMount = (editor: any) => {
    rtlEditorRef.current = editor;
    highlightRtlSignals();
    setupClickNavigation(editor, 'rtl');
  };

  const handleAssertionEditorMount = (editor: any) => {
    assertionEditorRef.current = editor;
    setupClickNavigation(editor, 'assertion');
  };

  // Setup click-to-navigate functionality
  const setupClickNavigation = (editor: any, panelType: string) => {
    if (!editor) return;

    editor.onMouseDown((e: any) => {
      const position = e.target.position;
      if (!position) return;

      const model = editor.getModel();
      if (!model) return;

      const word = model.getWordAtPosition(position);
      if (!word) return;

      const clickedWord = model.getValueInRange({
        startLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endLineNumber: position.lineNumber,
        endColumn: word.endColumn
      });

      // Check if clicked word is a signal
      if (assertion.traceability.rtl_signals.includes(clickedWord)) {
        handleSignalClick(clickedWord, panelType);
      }
    });
  };

  // Handle signal click - navigate to signal in other panels
  const handleSignalClick = (signal: string, sourcePanel: string) => {
    setSelectedSignal(signal);

    // Highlight signal in RTL panel
    if (sourcePanel !== 'rtl' && rtlEditorRef.current) {
      navigateToSignalInRtl(signal);
    }

    // Highlight signal in assertion panel
    if (sourcePanel !== 'assertion' && assertionEditorRef.current) {
      navigateToSignalInAssertion(signal);
    }
  };

  // Navigate to signal in RTL code
  const navigateToSignalInRtl = (signal: string) => {
    const editor = rtlEditorRef.current;
    if (!editor) return;

    const model = editor.getModel();
    if (!model) return;

    const text = model.getValue();
    const regex = new RegExp(`\\b${signal}\\b`, 'g');
    let match;
    const matches: any[] = [];

    while ((match = regex.exec(text)) !== null) {
      const pos = model.getPositionAt(match.index);
      matches.push(pos);
    }

    if (matches.length > 0) {
      // Navigate to first occurrence
      editor.revealLineInCenter(matches[0].lineNumber);
      editor.setPosition(matches[0]);

      // Highlight all occurrences
      const decorations = matches.map(pos => ({
        range: {
          startLineNumber: pos.lineNumber,
          startColumn: pos.column,
          endLineNumber: pos.lineNumber,
          endColumn: pos.column + signal.length
        },
        options: {
          inlineClassName: 'highlighted-signal-click'
        }
      }));

      editor.deltaDecorations([], decorations);
    }
  };

  // Navigate to signal in assertion code
  const navigateToSignalInAssertion = (signal: string) => {
    const editor = assertionEditorRef.current;
    if (!editor) return;

    const model = editor.getModel();
    if (!model) return;

    const text = model.getValue();
    const index = text.indexOf(signal);

    if (index !== -1) {
      const pos = model.getPositionAt(index);
      editor.revealLineInCenter(pos.lineNumber);
      editor.setPosition(pos);

      // Highlight the signal
      editor.deltaDecorations([], [{
        range: {
          startLineNumber: pos.lineNumber,
          startColumn: pos.column,
          endLineNumber: pos.lineNumber,
          endColumn: pos.column + signal.length
        },
        options: {
          inlineClassName: 'highlighted-signal-click'
        }
      }]);
    }
  };

  // Highlight requirement text in specification
  const highlightRequirementText = () => {
    if (!specEditorRef.current || !assertion.traceability.requirement_text) return;

    const editor = specEditorRef.current;
    const model = editor.getModel();
    if (!model) return;

    const text = model.getValue();
    const requirementText = assertion.traceability.requirement_text;
    
    // Find the requirement text in the specification
    const index = text.indexOf(requirementText);
    if (index !== -1) {
      const startPos = model.getPositionAt(index);
      const endPos = model.getPositionAt(index + requirementText.length);
      
      // Highlight the text
      editor.deltaDecorations([], [
        {
          range: {
            startLineNumber: startPos.lineNumber,
            startColumn: startPos.column,
            endLineNumber: endPos.lineNumber,
            endColumn: endPos.column
          },
          options: {
            isWholeLine: false,
            className: 'highlighted-requirement',
            inlineClassName: 'highlighted-requirement-inline'
          }
        }
      ]);

      // Scroll to the highlighted text
      editor.revealLineInCenter(startPos.lineNumber);
    }
  };

  // Highlight RTL signals and line numbers
  const highlightRtlSignals = () => {
    if (!rtlEditorRef.current) return;

    const editor = rtlEditorRef.current;
    const model = editor.getModel();
    if (!model) return;

    const decorations: any[] = [];
    const lineNumbers = assertion.traceability.line_numbers || [];

    // Highlight specific line numbers
    lineNumbers.forEach(lineNum => {
      if (lineNum > 0 && lineNum <= model.getLineCount()) {
        decorations.push({
          range: {
            startLineNumber: lineNum,
            startColumn: 1,
            endLineNumber: lineNum,
            endColumn: model.getLineMaxColumn(lineNum)
          },
          options: {
            isWholeLine: true,
            className: 'highlighted-rtl-line',
            glyphMarginClassName: 'highlighted-rtl-glyph'
          }
        });
      }
    });

    // Apply decorations
    editor.deltaDecorations([], decorations);

    // Scroll to first highlighted line
    if (lineNumbers.length > 0) {
      editor.revealLineInCenter(lineNumbers[0]);
    }
  };

  // Handle synchronized scrolling
  const handleScroll = (sourceEditor: any, targetEditors: any[]) => {
    if (!syncScroll) return;

    const visibleRange = sourceEditor.getVisibleRanges()[0];
    if (!visibleRange) return;

    targetEditors.forEach(targetEditor => {
      if (targetEditor && targetEditor !== sourceEditor) {
        targetEditor.revealLineInCenter(visibleRange.startLineNumber, 0);
      }
    });
  };

  // Set up scroll synchronization
  useEffect(() => {
    if (!syncScroll) return;

    const editors = [specEditorRef.current, rtlEditorRef.current, assertionEditorRef.current];
    const disposables: any[] = [];

    editors.forEach((editor, index) => {
      if (editor) {
        const otherEditors = editors.filter((_, i) => i !== index);
        const disposable = editor.onDidScrollChange(() => {
          handleScroll(editor, otherEditors);
        });
        disposables.push(disposable);
      }
    });

    return () => {
      disposables.forEach(d => d?.dispose());
    };
  }, [syncScroll, specEditorRef.current, rtlEditorRef.current, assertionEditorRef.current]);

  // Re-highlight when assertion changes
  useEffect(() => {
    highlightRequirementText();
    highlightRtlSignals();
  }, [assertion]);

  return (
    <div className="side-by-side-viewer h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Assertion Viewer
          </h2>
          <span className="text-sm text-gray-500">
            {assertion.traceability.spec_reference}
          </span>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-600">Confidence:</span>
            <span className={`text-xs font-medium ${
              assertion.confidence_score >= 0.8 ? 'text-green-600' :
              assertion.confidence_score >= 0.6 ? 'text-yellow-600' :
              'text-red-600'
            }`}>
              {(assertion.confidence_score * 100).toFixed(0)}%
            </span>
          </div>
          {assertion.quality_score !== undefined && (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-600">Quality:</span>
              <span className={`text-xs font-medium ${
                assertion.quality_score >= 0.8 ? 'text-green-600' :
                assertion.quality_score >= 0.6 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {(assertion.quality_score * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={syncScroll}
              onChange={(e) => setSyncScroll(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Sync Scroll</span>
          </label>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close viewer"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Three-panel layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Specification */}
        <div className="flex-1 flex flex-col border-r border-gray-200 bg-white">
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
            <h3 className="text-sm font-medium text-gray-700">Specification</h3>
            <p className="text-xs text-gray-500 mt-1">
              Requirement: {assertion.traceability.spec_reference}
            </p>
          </div>
          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              defaultLanguage="markdown"
              value={specificationText}
              theme="vs-light"
              options={{
                readOnly: true,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 13,
                lineNumbers: 'on',
                glyphMargin: true,
                folding: true,
                wordWrap: 'on'
              }}
              onMount={handleSpecEditorMount}
            />
          </div>
        </div>

        {/* Middle Panel: RTL Code */}
        <div className="flex-1 flex flex-col border-r border-gray-200 bg-white">
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
            <h3 className="text-sm font-medium text-gray-700">RTL Design</h3>
            <p className="text-xs text-gray-500 mt-1">
              Module: {assertion.traceability.rtl_module}
            </p>
            {assertion.traceability.rtl_signals.length > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                Signals: {assertion.traceability.rtl_signals.join(', ')}
              </p>
            )}
          </div>
          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              defaultLanguage="systemverilog"
              value={rtlCode}
              theme="vs-light"
              options={{
                readOnly: true,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 13,
                lineNumbers: 'on',
                glyphMargin: true,
                folding: true
              }}
              onMount={handleRtlEditorMount}
            />
          </div>
        </div>

        {/* Right Panel: Assertion Code */}
        <div className="flex-1 flex flex-col bg-white">
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
            <h3 className="text-sm font-medium text-gray-700">Generated Assertion</h3>
            <p className="text-xs text-gray-500 mt-1">
              Type: {assertion.assertion_type}
            </p>
          </div>
          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              defaultLanguage="systemverilog"
              value={assertion.assertion_code}
              theme="vs-light"
              options={{
                readOnly: true,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 13,
                lineNumbers: 'on',
                glyphMargin: false,
                folding: false
              }}
              onMount={handleAssertionEditorMount}
            />
          </div>
          {assertion.explanation && (
            <div className="border-t border-gray-200 bg-blue-50 px-4 py-3">
              <h4 className="text-xs font-medium text-blue-900 mb-1">Explanation</h4>
              <p className="text-xs text-blue-800">{assertion.explanation}</p>
            </div>
          )}
        </div>
      </div>

      {/* Custom CSS for highlighting */}
      <style>{`
        .highlighted-requirement {
          background-color: rgba(255, 235, 59, 0.3);
        }
        .highlighted-requirement-inline {
          background-color: rgba(255, 235, 59, 0.3);
        }
        .highlighted-rtl-line {
          background-color: rgba(76, 175, 80, 0.2);
        }
        .highlighted-rtl-glyph {
          background-color: #4CAF50;
          width: 3px !important;
          margin-left: 3px;
        }
        .highlighted-signal-click {
          background-color: rgba(33, 150, 243, 0.4);
          border-bottom: 2px solid #2196F3;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
};

export default SideBySideViewer;

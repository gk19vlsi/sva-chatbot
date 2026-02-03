import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { validateSVASyntax, ValidationResult } from '../utils/svaValidator';

/**
 * Assertion data interface
 */
export interface Assertion {
  id: string;
  code: string;
  type: 'immediate' | 'concurrent' | 'property' | 'sequence';
  category: string;
  confidenceScore: number;
  qualityScore?: number;
  explanation: string;
  displayName?: string; // Optional display name like "Assertion 1"
  traceability?: {
    requirementText: string;
    rtlSignals: string[];
    rtlModule: string;
  };
}

interface AssertionViewerProps {
  assertion: Assertion;
  readOnly?: boolean;
  onCodeChange?: (code: string) => void;
  onSave?: (code: string) => Promise<void>;
  onCancel?: () => void;
  enableEdit?: boolean;
  enableFeedback?: boolean;
  onFeedbackSubmit?: (rating: number, comment: string) => Promise<void>;
}

/**
 * AssertionViewer Component
 * Displays SystemVerilog assertions with syntax highlighting and metadata
 * Supports edit mode with save and cancel functionality
 * 
 * Validates: Requirements 10.1, 10.2, 14.1, 14.5
 */
const AssertionViewer: React.FC<AssertionViewerProps> = ({
  assertion,
  readOnly = true,
  onCodeChange,
  onSave,
  onCancel,
  enableEdit = false,
  enableFeedback = false,
  onFeedbackSubmit,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedCode, setEditedCode] = useState(assertion.code);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  
  // Feedback state
  const [showFeedback, setShowFeedback] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState('');
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);
  
  // Clipboard copy state
  const [copySuccess, setCopySuccess] = useState(false);

  // Validate code when it changes in edit mode
  useEffect(() => {
    if (isEditing && editedCode) {
      const result = validateSVASyntax(editedCode);
      setValidationResult(result);
    } else {
      setValidationResult(null);
    }
  }, [isEditing, editedCode]);

  /**
   * Handle editor content change
   */
  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setEditedCode(value);
      if (onCodeChange) {
        onCodeChange(value);
      }
    }
  };

  /**
   * Handle edit button click
   */
  const handleEditClick = () => {
    setIsEditing(true);
    setEditedCode(assertion.code);
    setSaveError(null);
  };

  /**
   * Handle save button click
   */
  const handleSaveClick = async () => {
    if (!onSave) return;

    try {
      setIsSaving(true);
      setSaveError(null);
      await onSave(editedCode);
      setIsEditing(false);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save assertion');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Handle cancel button click
   */
  const handleCancelClick = () => {
    setEditedCode(assertion.code);
    setIsEditing(false);
    setSaveError(null);
    if (onCancel) {
      onCancel();
    }
  };

  /**
   * Handle feedback submission
   */
  const handleFeedbackSubmit = async () => {
    if (!onFeedbackSubmit || rating === 0) return;

    try {
      setIsSubmittingFeedback(true);
      setFeedbackError(null);
      await onFeedbackSubmit(rating, comment);
      setFeedbackSuccess(true);
      
      // Reset form after 2 seconds
      setTimeout(() => {
        setShowFeedback(false);
        setRating(0);
        setComment('');
        setFeedbackSuccess(false);
      }, 2000);
    } catch (error) {
      setFeedbackError(error instanceof Error ? error.message : 'Failed to submit feedback');
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  /**
   * Handle feedback toggle
   */
  const handleFeedbackToggle = () => {
    setShowFeedback(!showFeedback);
    setFeedbackError(null);
    setFeedbackSuccess(false);
  };

  /**
   * Handle clipboard copy
   * Validates: Requirements 15.4
   */
  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(currentCode);
      setCopySuccess(true);
      
      // Reset success message after 2 seconds
      setTimeout(() => {
        setCopySuccess(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      // Fallback for older browsers
      try {
        const textArea = document.createElement('textarea');
        textArea.value = currentCode;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        setCopySuccess(true);
        setTimeout(() => {
          setCopySuccess(false);
        }, 2000);
      } catch (fallbackError) {
        console.error('Fallback copy failed:', fallbackError);
      }
    }
  };

  /**
   * Get score color based on value
   */
  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  /**
   * Get assertion type badge color
   */
  const getTypeBadgeColor = (type: string): string => {
    switch (type) {
      case 'immediate':
        return 'bg-blue-100 text-blue-800';
      case 'concurrent':
        return 'bg-purple-100 text-purple-800';
      case 'property':
        return 'bg-indigo-100 text-indigo-800';
      case 'sequence':
        return 'bg-pink-100 text-pink-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const currentCode = isEditing ? editedCode : assertion.code;
  const isReadOnly = readOnly || !isEditing;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Header with metadata */}
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-gray-900">
              {assertion.displayName || `Assertion ${assertion.id}`}
            </h3>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${getTypeBadgeColor(
                assertion.type
              )}`}
            >
              {assertion.type}
            </span>
            <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
              {assertion.category}
            </span>
            {isEditing && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800">
                Editing
              </span>
            )}
          </div>

          {/* Scores and Edit Button */}
          <div className="flex items-center space-x-4">
            {/* Confidence Score */}
            <div
              className={`px-3 py-1 rounded border ${getScoreColor(
                assertion.confidenceScore
              )}`}
            >
              <span className="text-xs font-medium">Confidence:</span>
              <span className="ml-1 text-sm font-bold">
                {(assertion.confidenceScore * 100).toFixed(0)}%
              </span>
            </div>

            {/* Quality Score */}
            {assertion.qualityScore !== undefined && (
              <div
                className={`px-3 py-1 rounded border ${getScoreColor(
                  assertion.qualityScore
                )}`}
              >
                <span className="text-xs font-medium">Quality:</span>
                <span className="ml-1 text-sm font-bold">
                  {(assertion.qualityScore * 100).toFixed(0)}%
                </span>
              </div>
            )}

            {/* Edit Button */}
            {enableEdit && !readOnly && !isEditing && (
              <button
                onClick={handleEditClick}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Edit
              </button>
            )}
            
            {/* Copy Button */}
            <button
              onClick={handleCopyToClipboard}
              className="px-3 py-1 bg-gray-600 text-white rounded text-sm font-medium hover:bg-gray-700 transition-colors flex items-center space-x-1"
              title="Copy assertion code to clipboard"
            >
              {copySuccess ? (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Explanation */}
        {assertion.explanation && (
          <p className="text-sm text-gray-600 mt-2">{assertion.explanation}</p>
        )}
      </div>

      {/* Code Editor */}
      <div className="relative">
        <Editor
          height="200px"
          defaultLanguage="systemverilog"
          value={currentCode}
          onChange={handleEditorChange}
          options={{
            readOnly: isReadOnly,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            lineNumbers: 'on',
            renderLineHighlight: 'all',
            automaticLayout: true,
            wordWrap: 'on',
            theme: 'vs-light',
          }}
          theme="vs-light"
        />
        
        {/* Validation Errors Overlay */}
        {isEditing && validationResult && !validationResult.isValid && (
          <div className="absolute top-2 right-2 bg-red-50 border border-red-200 rounded-lg p-2 max-w-md shadow-lg">
            <div className="flex items-start space-x-2">
              <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-800 mb-1">Syntax Errors</h4>
                <ul className="text-xs text-red-700 space-y-1">
                  {validationResult.errors.filter(e => e.severity === 'error').map((error, index) => (
                    <li key={index}>
                      Line {error.line}: {error.message}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
        
        {/* Validation Success Indicator */}
        {isEditing && validationResult && validationResult.isValid && (
          <div className="absolute top-2 right-2 bg-green-50 border border-green-200 rounded-lg p-2 shadow-lg">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-sm font-medium text-green-800">Syntax Valid</span>
            </div>
          </div>
        )}
      </div>

      {/* Edit Mode Actions */}
      {isEditing && (
        <div className="bg-gray-50 border-t border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={handleSaveClick}
                disabled={isSaving || !!(validationResult && !validationResult.isValid)}
                className="px-4 py-2 bg-green-600 text-white rounded font-medium hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                title={validationResult && !validationResult.isValid ? 'Fix syntax errors before saving' : ''}
              >
                {isSaving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={handleCancelClick}
                disabled={isSaving}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded font-medium hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
              >
                Cancel
              </button>
              {validationResult && !validationResult.isValid && (
                <span className="text-sm text-red-600">
                  {validationResult.errors.filter(e => e.severity === 'error').length} error(s) found
                </span>
              )}
            </div>
            {saveError && (
              <div className="text-sm text-red-600">
                {saveError}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Traceability Information */}
      {assertion.traceability && (
        <div className="bg-gray-50 border-t border-gray-200 px-4 py-3">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">
            Traceability
          </h4>

          {/* Requirement */}
          <div className="mb-3">
            <span className="text-xs font-medium text-gray-500 uppercase">
              Requirement:
            </span>
            <p className="text-sm text-gray-700 mt-1">
              {assertion.traceability.requirementText}
            </p>
          </div>

          {/* RTL Module */}
          <div className="mb-2">
            <span className="text-xs font-medium text-gray-500 uppercase">
              RTL Module:
            </span>
            <span className="ml-2 text-sm text-gray-900 font-mono">
              {assertion.traceability.rtlModule}
            </span>
          </div>

          {/* RTL Signals */}
          {assertion.traceability.rtlSignals.length > 0 && (
            <div>
              <span className="text-xs font-medium text-gray-500 uppercase">
                RTL Signals:
              </span>
              <div className="flex flex-wrap gap-2 mt-1">
                {assertion.traceability.rtlSignals.map((signal, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-mono"
                  >
                    {signal}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Feedback Section */}
      {enableFeedback && !readOnly && (
        <div className="border-t border-gray-200">
          {!showFeedback ? (
            <button
              onClick={handleFeedbackToggle}
              className="w-full px-4 py-3 text-left text-sm font-medium text-blue-600 hover:bg-blue-50 transition-colors flex items-center justify-between"
            >
              <span>Provide Feedback</span>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          ) : (
            <div className="bg-gray-50 px-4 py-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-gray-900">
                  Rate this assertion
                </h4>
                <button
                  onClick={handleFeedbackToggle}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Star Rating */}
              <div className="flex items-center space-x-1 mb-4">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    className="focus:outline-none transition-transform hover:scale-110"
                  >
                    <svg
                      className={`w-8 h-8 ${
                        star <= (hoverRating || rating)
                          ? 'text-yellow-400 fill-current'
                          : 'text-gray-300'
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                      />
                    </svg>
                  </button>
                ))}
                {rating > 0 && (
                  <span className="ml-2 text-sm text-gray-600">
                    {rating} star{rating !== 1 ? 's' : ''}
                  </span>
                )}
              </div>

              {/* Comment Text Area */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Comments (optional)
                </label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Share your thoughts about this assertion..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>

              {/* Submit Button */}
              <div className="flex items-center justify-between">
                <button
                  onClick={handleFeedbackSubmit}
                  disabled={rating === 0 || isSubmittingFeedback}
                  className="px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm"
                >
                  {isSubmittingFeedback ? 'Submitting...' : 'Submit Feedback'}
                </button>
                
                {feedbackError && (
                  <span className="text-sm text-red-600">{feedbackError}</span>
                )}
                
                {feedbackSuccess && (
                  <span className="text-sm text-green-600 flex items-center">
                    <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Thank you!
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AssertionViewer;

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import api from '../services/api';

/**
 * File upload types
 */
export type FileType = 'specification' | 'rtl';

interface UploadedFile {
  file: File;
  id: string;
  progress: number;
  status: 'uploading' | 'complete' | 'error';
  error?: string;
}

interface FileUploadProps {
  fileType: FileType;
  projectId?: string;
  onUploadComplete?: (fileId: string) => void;
  onUploadError?: (error: Error) => void;
}

/**
 * FileUpload Component
 * Handles file uploads with drag-and-drop, validation, and progress tracking
 * 
 * Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5
 */
const FileUpload: React.FC<FileUploadProps> = ({
  fileType,
  projectId,
  onUploadComplete,
  onUploadError,
}) => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

  // Define accepted file types based on fileType prop
  const acceptedFileTypes = fileType === 'specification'
    ? {
        'application/pdf': ['.pdf'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'application/msword': ['.doc'],
        'text/markdown': ['.md'],
        'text/plain': ['.txt'],
      }
    : {
        'text/x-systemverilog': ['.sv'],
        'text/x-verilog': ['.v'],
      };

  // Maximum file size: 50MB
  const maxSize = 50 * 1024 * 1024;

  /**
   * Validate file type and size
   * Validates: Requirements 13.4
   */
  const validateFile = (file: File): { valid: boolean; error?: string } => {
    // Check file size
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `File size exceeds 50MB limit (${(file.size / 1024 / 1024).toFixed(2)}MB)`,
      };
    }

    // Check file extension
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    const validExtensions = fileType === 'specification'
      ? ['.pdf', '.docx', '.doc', '.md', '.txt']
      : ['.sv', '.v'];

    if (!validExtensions.includes(extension)) {
      return {
        valid: false,
        error: `Invalid file type. Accepted: ${validExtensions.join(', ')}`,
      };
    }

    return { valid: true };
  };

  /**
   * Upload file to backend API
   * Validates: Requirements 13.2, 13.5
   */
  const uploadFile = async (file: File, fileId: string): Promise<void> => {
    if (!projectId) {
      throw new Error('Project ID is required for file upload');
    }

    const formData = new FormData();
    formData.append('file', file);

    const endpoint = fileType === 'specification'
      ? `/api/projects/${projectId}/upload-spec`
      : `/api/projects/${projectId}/upload-rtl`;

    try {
      const response = await api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadedFiles(prev =>
              prev.map(f =>
                f.id === fileId
                  ? { ...f, progress }
                  : f
              )
            );
          }
        },
      });

      // Mark as complete
      setUploadedFiles(prev =>
        prev.map(f =>
          f.id === fileId
            ? { ...f, status: 'complete', progress: 100 }
            : f
        )
      );

      // Call success callback with the uploaded file ID from backend
      if (onUploadComplete && response.data.id) {
        onUploadComplete(response.data.id);
      }
    } catch (error) {
      // Mark as error
      setUploadedFiles(prev =>
        prev.map(f =>
          f.id === fileId
            ? { 
                ...f, 
                status: 'error', 
                error: error instanceof Error ? error.message : 'Upload failed' 
              }
            : f
        )
      );
      throw error;
    }
  };

  /**
   * Handle file drop
   * Validates: Requirements 13.1, 13.3, 13.4
   */
  const onDrop = useCallback(
    async (acceptedFiles: File[], rejectedFiles: any[]) => {
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        rejectedFiles.forEach(({ file, errors }) => {
          const errorMessage = errors.map((e: any) => e.message).join(', ');
          const error = new Error(`${file.name}: ${errorMessage}`);
          if (onUploadError) {
            onUploadError(error);
          }
        });
      }

      // Process accepted files
      for (const file of acceptedFiles) {
        // Validate file
        const validation = validateFile(file);
        if (!validation.valid) {
          const error = new Error(validation.error);
          if (onUploadError) {
            onUploadError(error);
          }
          continue;
        }

        // Add file to upload list
        const fileId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const uploadedFile: UploadedFile = {
          file,
          id: fileId,
          progress: 0,
          status: 'uploading',
        };

        setUploadedFiles(prev => [...prev, uploadedFile]);

        // Start upload
        try {
          await uploadFile(file, fileId);
        } catch (error) {
          setUploadedFiles(prev =>
            prev.map(f =>
              f.id === fileId
                ? { ...f, status: 'error', error: 'Upload failed' }
                : f
            )
          );
          if (onUploadError) {
            onUploadError(error as Error);
          }
        }
      }
    },
    [fileType, onUploadComplete, onUploadError]
  );

  // Configure dropzone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFileTypes as any,
    maxSize,
    multiple: true,
  });

  /**
   * Remove uploaded file
   */
  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  /**
   * Get file icon based on extension
   */
  const getFileIcon = (fileName: string): string => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return '📄';
      case 'docx':
      case 'doc':
        return '📝';
      case 'md':
        return '📋';
      case 'txt':
        return '📃';
      case 'sv':
      case 'v':
        return '⚡';
      default:
        return '📁';
    }
  };

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }
        `}
      >
        <input {...getInputProps()} />
        
        <div className="text-6xl mb-4">
          {fileType === 'specification' ? '📄' : '⚡'}
        </div>

        {isDragActive ? (
          <p className="text-lg text-blue-600 font-medium">
            Drop files here...
          </p>
        ) : (
          <>
            <p className="text-lg text-gray-700 mb-2">
              Drag & drop {fileType === 'specification' ? 'specification' : 'RTL'} files here
            </p>
            <p className="text-sm text-gray-500 mb-4">
              or click to browse
            </p>
            <p className="text-xs text-gray-400">
              {fileType === 'specification'
                ? 'Accepted formats: PDF, DOCX, MD, TXT'
                : 'Accepted formats: .sv, .v'
              }
              <br />
              Maximum file size: 50MB
            </p>
          </>
        )}
      </div>

      {/* Uploaded files list */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-700">
            Uploaded Files ({uploadedFiles.length})
          </h3>
          
          {uploadedFiles.map((uploadedFile) => (
            <div
              key={uploadedFile.id}
              className="bg-white border border-gray-200 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <span className="text-2xl">
                    {getFileIcon(uploadedFile.file.name)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {uploadedFile.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(uploadedFile.file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>

                {/* Status indicator */}
                <div className="flex items-center space-x-2">
                  {uploadedFile.status === 'uploading' && (
                    <span className="text-xs text-blue-600">
                      {uploadedFile.progress}%
                    </span>
                  )}
                  {uploadedFile.status === 'complete' && (
                    <span className="text-green-600 text-xl">✓</span>
                  )}
                  {uploadedFile.status === 'error' && (
                    <span className="text-red-600 text-xl">✗</span>
                  )}
                  
                  <button
                    onClick={() => removeFile(uploadedFile.id)}
                    className="text-gray-400 hover:text-red-600 transition-colors"
                    title="Remove file"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Progress bar */}
              {uploadedFile.status === 'uploading' && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadedFile.progress}%` }}
                  />
                </div>
              )}

              {/* Error message */}
              {uploadedFile.status === 'error' && uploadedFile.error && (
                <p className="text-xs text-red-600 mt-1">
                  {uploadedFile.error}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;

import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Home page component
 * Landing page with introduction and quick actions
 */
const Home: React.FC = () => {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="bg-white shadow rounded-lg p-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to SVA-Chatbot
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          AI-powered SystemVerilog Assertion Generation from Natural Language Specifications
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          {/* Feature 1 */}
          <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
            <div className="text-blue-600 text-3xl mb-4">📄</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Upload Specifications
            </h3>
            <p className="text-gray-600 mb-4">
              Upload your specification documents in PDF, DOCX, Markdown, or plain text format.
            </p>
            <Link
              to="/upload"
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Get Started →
            </Link>
          </div>

          {/* Feature 2 */}
          <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
            <div className="text-blue-600 text-3xl mb-4">🤖</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              AI-Powered Generation
            </h3>
            <p className="text-gray-600 mb-4">
              Our multi-agent AI system analyzes your specs and RTL to generate precise assertions.
            </p>
            <Link
              to="/projects"
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              View Projects →
            </Link>
          </div>

          {/* Feature 3 */}
          <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
            <div className="text-blue-600 text-3xl mb-4">✅</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Review & Export
            </h3>
            <p className="text-gray-600 mb-4">
              Review generated assertions with full traceability and export for your verification environment.
            </p>
            <Link
              to="/assertions"
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              View Assertions →
            </Link>
          </div>
        </div>

        {/* Quick start section */}
        <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Quick Start
          </h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-700">
            <li>Create a new project or select an existing one</li>
            <li>Upload your specification documents and RTL files</li>
            <li>Let the AI agents analyze and generate assertions</li>
            <li>Review, edit, and provide feedback on generated assertions</li>
            <li>Export assertions with traceability for integration</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default Home;

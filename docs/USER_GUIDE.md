# SVA-Chatbot User Guide

Welcome to SVA-Chatbot! This guide will help you get started with automatically generating SystemVerilog Assertions from your specifications and RTL designs.

## Table of Contents

1. [Getting Started](#getting-started)
2. [File Upload Process](#file-upload-process)
3. [Assertion Review Workflow](#assertion-review-workflow)
4. [Export Process](#export-process)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

## Getting Started

### What is SVA-Chatbot?

SVA-Chatbot is an AI-powered tool that automatically generates SystemVerilog Assertions (SVA) from:

- Natural language specifications (PDF, DOCX, Markdown, TXT)
- RTL design files (SystemVerilog)

The system uses advanced AI to understand your requirements and generate high-quality assertions with full traceability.

### System Requirements

**Supported Browsers:**

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Supported File Formats:**

- **Specifications**: PDF, DOCX, MD, TXT
- **RTL**: .sv, .v (SystemVerilog/Verilog)

**File Size Limits:**

- Maximum file size: 50 MB
- Recommended: Keep files under 10 MB for faster processing

### First Time Setup

1. **Access the Application**
   - Open your browser and navigate to the application URL
   - Development: `http://localhost:3000`
   - Production: `https://your-domain.com`

2. **Create an Account**
   - Click "Sign Up" on the login page
   - Enter your email and create a password
   - Verify your email address

3. **Log In**
   - Enter your credentials
   - You'll be redirected to the dashboard

## File Upload Process

### Step 1: Create a Project

1. Click "New Project" on the dashboard
2. Enter project details:
   - **Name**: Descriptive project name (e.g., "AXI Protocol Verification")
   - **Description**: Brief description of what you're verifying
3. Click "Create Project"

### Step 2: Upload Specification

1. Click on your project to open it
2. Navigate to the "Specifications" tab
3. Click "Upload Specification" or drag and drop your file
4. Supported formats:
   - **PDF**: Specification documents, datasheets
   - **DOCX**: Word documents with requirements
   - **Markdown**: Structured specification files
   - **TXT**: Plain text requirements

**Tips for Better Results:**

- Use clear, structured specifications
- Include temporal keywords (after, within, before, eventually)
- Number your requirements for easy reference
- Avoid ambiguous language

**Example Good Specification:**

```
Requirement 1.1: The slave MUST respond to AWVALID within 16 clock cycles.
Requirement 1.2: AWREADY MUST remain stable until AWVALID is asserted.
Requirement 1.3: The write data MUST be valid when WVALID is high.
```

### Step 3: Upload RTL Design

1. Navigate to the "RTL Designs" tab
2. Click "Upload RTL" or drag and drop your file
3. Supported formats:
   - **.sv**: SystemVerilog files
   - **.v**: Verilog files

**Tips for Better Results:**

- Use clear signal names that match your specification
- Include comments in your RTL
- Ensure your RTL is syntactically correct
- Use standard naming conventions (clk, rst_n, etc.)

**Example RTL Structure:**

```systemverilog
module axi_slave (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        awvalid,
  output logic        awready,
  // ... more signals
);
```

### Step 4: Start Generation

1. Once both specification and RTL are uploaded, click "Generate Assertions"
2. The system will process your files through a multi-agent pipeline:
   - **Specification Parser**: Extracts requirements
   - **RTL Analyzer**: Analyzes your design
   - **Alignment Agent**: Maps requirements to RTL
   - **SVA Generator**: Creates assertions
   - **Validator**: Checks quality

3. Monitor progress in real-time:
   - See which agent is currently running
   - View status messages
   - Answer clarification questions if needed

**Processing Time:**

- Small projects (< 10 requirements): 1-2 minutes
- Medium projects (10-50 requirements): 2-5 minutes
- Large projects (50+ requirements): 5-15 minutes

## Assertion Review Workflow

### Understanding the Assertion Viewer

Once generation is complete, you'll see the Assertion Viewer with three panels:

**Left Panel: Specification**

- Shows your original requirements
- Highlights the requirement for the selected assertion
- Click to navigate between requirements

**Middle Panel: RTL Code**

- Shows relevant RTL code
- Highlights signals used in the assertion
- Shows line numbers for traceability

**Right Panel: Assertion Code**

- Shows the generated SVA code
- Includes comments explaining the assertion
- Displays confidence and quality scores

### Reviewing Assertions

For each assertion, check:

1. **Correctness**
   - Does it match the requirement?
   - Are the signals correct?
   - Is the timing correct?

2. **Quality Scores**
   - **Confidence Score**: How confident the AI is (0.0-1.0)
   - **Quality Score**: Assertion quality rating (0.0-1.0)
   - Higher scores indicate better assertions

3. **Traceability**
   - Requirement reference
   - RTL signals used
   - Line numbers in RTL

### Editing Assertions

If you need to modify an assertion:

1. Click the "Edit" button
2. Make your changes in the code editor
3. The system validates syntax in real-time
4. Click "Save" to update the assertion
5. The assertion is marked as "Modified"

**Example Edit:**

```systemverilog
// Original (16 cycle timeout)
assert property (@(posedge clk) disable iff (!rst_n)
  awvalid |-> ##[1:16] awready
);

// Modified (8 cycle timeout)
assert property (@(posedge clk) disable iff (!rst_n)
  awvalid |-> ##[1:8] awready
);
```

### Providing Feedback

Help improve the system by providing feedback:

1. Click the "Feedback" button on an assertion
2. Rate the assertion (1-5 stars)
3. Add comments (optional)
4. Click "Submit"

Your feedback helps the AI learn and improve future generations.

### Regenerating Assertions

If an assertion isn't quite right:

1. Click "Regenerate" on the assertion
2. Optionally provide guidance in the chat
3. The system will generate a new version
4. Compare and choose the best version

## Export Process

### Exporting Assertions

Once you're satisfied with your assertions:

1. Click "Export" in the toolbar
2. Choose export format:
   - **SVA File**: Ready to integrate into your testbench
   - **JSON**: For programmatic processing
   - **Markdown**: For documentation

3. Configure export options:
   - Include comments (recommended)
   - Include traceability information
   - Add integration instructions

4. Click "Download"

### SVA File Format

The exported SVA file includes:

```systemverilog
// ============================================
// SVA-Chatbot Generated Assertions
// Project: AXI Protocol Verification
// Generated: 2026-01-17T00:00:00.000000
// ============================================

// Requirement 1.1: The slave MUST respond to AWVALID within 16 clock cycles
// Confidence: 0.92, Quality: 0.88
// Signals: awvalid, awready
// Module: axi_slave (lines 45-67)
assert property (@(posedge clk) disable iff (!rst_n)
  awvalid |-> ##[1:16] awready
) else $error("AWVALID timeout");

// ... more assertions ...

// ============================================
// Integration Instructions
// ============================================
// 1. Include this file in your testbench
// 2. Bind assertions to your DUT
// 3. Run simulation with assertions enabled
```

### Exporting Traceability Report

Generate a traceability matrix:

1. Click "Export" → "Traceability Report"
2. Choose format:
   - **JSON**: Machine-readable
   - **CSV**: Spreadsheet-compatible
   - **Markdown**: Human-readable

3. The report includes:
   - Requirement-to-assertion mapping
   - Coverage statistics
   - Signal references
   - Quality metrics

### Copying Individual Assertions

To copy a single assertion:

1. Click the "Copy" button on the assertion
2. The code is copied to your clipboard
3. Paste into your testbench or documentation

## Best Practices

### Writing Better Specifications

**Do:**

- ✅ Use clear, unambiguous language
- ✅ Include temporal keywords (within, after, before)
- ✅ Number your requirements
- ✅ Specify timing constraints explicitly
- ✅ Use consistent terminology

**Don't:**

- ❌ Use vague terms like "quickly" or "soon"
- ❌ Mix multiple requirements in one sentence
- ❌ Use ambiguous pronouns (it, this, that)
- ❌ Omit timing information
- ❌ Use inconsistent signal names

**Example:**

❌ Bad: "The system should respond quickly when requested."

✅ Good: "The slave MUST assert awready within 16 clock cycles after awvalid is asserted."

### Organizing RTL Code

**Do:**

- ✅ Use descriptive signal names
- ✅ Add comments explaining functionality
- ✅ Follow consistent naming conventions
- ✅ Group related signals
- ✅ Use standard clock/reset names

**Don't:**

- ❌ Use cryptic abbreviations
- ❌ Mix naming conventions
- ❌ Omit comments
- ❌ Use inconsistent indentation

### Reviewing Generated Assertions

**Checklist:**

- [ ] Assertion matches the requirement
- [ ] Correct signals are referenced
- [ ] Timing is accurate
- [ ] Clock and reset are correct
- [ ] Assertion is not vacuous
- [ ] Assertion is not over-constrained
- [ ] Comments are clear
- [ ] Confidence score is acceptable (> 0.7)
- [ ] Quality score is acceptable (> 0.7)

### Integration Workflow

1. **Review**: Check all assertions carefully
2. **Edit**: Modify as needed
3. **Test**: Export and integrate into testbench
4. **Simulate**: Run with your RTL
5. **Debug**: Fix any issues
6. **Feedback**: Report results to improve the system

## Troubleshooting

### Upload Issues

**Problem**: File upload fails

**Solutions:**

- Check file size (< 50 MB)
- Verify file format is supported
- Ensure file is not corrupted
- Try a different browser
- Check internet connection

**Problem**: "Invalid file type" error

**Solutions:**

- Verify file extension (.pdf, .docx, .md, .txt, .sv, .v)
- Rename file with correct extension
- Convert file to supported format

### Generation Issues

**Problem**: Generation takes too long

**Solutions:**

- Large files take longer (5-15 minutes)
- Check status in the progress panel
- Refresh page if stuck > 20 minutes
- Contact support if issue persists

**Problem**: "No assertions generated"

**Solutions:**

- Check if specification has clear requirements
- Verify RTL is syntactically correct
- Ensure specification and RTL are related
- Try with simpler specification first

**Problem**: Low confidence scores

**Solutions:**

- Improve specification clarity
- Add more detail to requirements
- Use standard terminology
- Ensure RTL matches specification

### Quality Issues

**Problem**: Assertions don't match requirements

**Solutions:**

- Review the traceability information
- Check if signals are named correctly
- Verify timing constraints
- Edit assertions manually
- Provide feedback for improvement

**Problem**: Syntax errors in generated assertions

**Solutions:**

- Use the built-in syntax validator
- Check SystemVerilog version compatibility
- Edit assertions to fix syntax
- Report issue with feedback

## FAQ

### General Questions

**Q: What is SystemVerilog Assertion (SVA)?**

A: SVA is a formal verification language built into SystemVerilog that allows you to specify properties your design must satisfy. Assertions help catch bugs early and document design intent.

**Q: Do I need to know SVA to use this tool?**

A: No! The tool generates SVA for you. However, basic understanding helps with reviewing and editing assertions.

**Q: How accurate are the generated assertions?**

A: Accuracy depends on specification quality. With clear specifications, the system achieves 85-95% accuracy. Always review generated assertions.

**Q: Can I use this for commercial projects?**

A: Yes, subject to the license terms. Check the LICENSE file for details.

### Technical Questions

**Q: What SystemVerilog version is supported?**

A: The tool generates assertions compatible with SystemVerilog IEEE 1800-2017.

**Q: Can I upload multiple RTL files?**

A: Yes, upload all related RTL files for your design. The system analyzes them together.

**Q: How is my data stored?**

A: All data is stored securely in MongoDB. See our Privacy Policy for details.

**Q: Can I delete my projects?**

A: Yes, you can delete projects anytime. This permanently removes all associated data.

### Workflow Questions

**Q: Can I collaborate with team members?**

A: Project sharing is planned for a future release. Currently, projects are private to each user.

**Q: Can I export assertions in other formats?**

A: Currently supported: SVA, JSON, Markdown. Additional formats can be added based on demand.

**Q: How do I integrate assertions into my testbench?**

A: Include the exported SVA file in your testbench and bind assertions to your DUT. See the integration instructions in the exported file.

**Q: Can I reuse assertions across projects?**

A: Yes, export assertions and import them into new projects, or copy individual assertions.

## Getting Help

### Support Channels

**Documentation:**

- User Guide: This document
- API Documentation: `/docs/API.md`
- Developer Guide: `/docs/DEVELOPER.md`

**Community:**

- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share tips
- Email: support@your-domain.com

**Response Times:**

- Critical issues: 24 hours
- General questions: 2-3 business days
- Feature requests: Reviewed monthly

### Reporting Issues

When reporting an issue, include:

1. What you were trying to do
2. What happened instead
3. Steps to reproduce
4. Screenshots (if applicable)
5. Browser and version
6. Project ID (if relevant)

### Feature Requests

We welcome feature requests! Submit them via:

- GitHub Issues (label: enhancement)
- Email: features@your-domain.com
- User feedback form in the app

## Next Steps

Now that you know the basics:

1. **Create your first project**
2. **Upload a simple specification and RTL**
3. **Generate and review assertions**
4. **Export and integrate into your testbench**
5. **Provide feedback to help us improve**

Happy verifying! 🚀

---

**Version**: 1.0.0  
**Last Updated**: January 17, 2026  
**Feedback**: user-feedback@your-domain.com

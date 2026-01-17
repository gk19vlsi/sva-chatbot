/**
 * SystemVerilog Assertion Syntax Validator
 *
 * Provides client-side syntax validation for SVA code
 *
 * Validates: Requirements 10.1
 */

export interface ValidationError {
  line: number;
  column: number;
  message: string;
  severity: "error" | "warning";
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  message: string;
}

/**
 * Validate SVA syntax
 */
export function validateSVASyntax(code: string): ValidationResult {
  const errors: ValidationError[] = [];

  if (!code || !code.trim()) {
    return {
      isValid: false,
      errors: [
        {
          line: 1,
          column: 1,
          message: "Empty assertion code",
          severity: "error",
        },
      ],
      message: "Empty assertion code",
    };
  }

  // Check for assertion keywords
  const hasAssertion =
    /\bassert\b/.test(code) ||
    /\bassume\b/.test(code) ||
    /\bcover\b/.test(code);

  if (!hasAssertion) {
    errors.push({
      line: 1,
      column: 1,
      message: "Missing assertion keyword (assert, assume, or cover)",
      severity: "error",
    });
  }

  // Check for concurrent assertion with property
  if (/\bassert\s+property\b/.test(code)) {
    // Check for clock event
    const hasClockEvent = /@\s*\(\s*(posedge|negedge)\s+\w+\s*\)/.test(code);
    if (!hasClockEvent) {
      const line = findLineNumber(code, "assert property");
      errors.push({
        line,
        column: 1,
        message:
          "Concurrent assertion missing clock event (@(posedge clk) or @(negedge clk))",
        severity: "error",
      });
    }
  }

  // Check for balanced parentheses
  let parenCount = 0;
  let parenLine = 1;
  let parenCol = 1;

  for (let i = 0; i < code.length; i++) {
    const char = code[i];

    if (char === "\n") {
      parenLine++;
      parenCol = 1;
    } else {
      parenCol++;
    }

    if (char === "(") {
      parenCount++;
    } else if (char === ")") {
      parenCount--;
      if (parenCount < 0) {
        errors.push({
          line: parenLine,
          column: parenCol,
          message: "Unbalanced parentheses (too many closing parentheses)",
          severity: "error",
        });
        break;
      }
    }
  }

  if (parenCount > 0) {
    errors.push({
      line: parenLine,
      column: parenCol,
      message: "Unbalanced parentheses (unclosed opening parentheses)",
      severity: "error",
    });
  }

  // Check for semicolon at end
  if (!code.trim().endsWith(";")) {
    const lines = code.split("\n");
    errors.push({
      line: lines.length,
      column: lines[lines.length - 1].length + 1,
      message: "Missing semicolon at end of assertion",
      severity: "error",
    });
  }

  // Check for common mistakes
  if (/\|\->/.test(code)) {
    const line = findLineNumber(code, "|->");
    errors.push({
      line,
      column: 1,
      message: 'Did you mean "|->" instead of "|->"?',
      severity: "warning",
    });
  }

  const isValid = errors.filter((e) => e.severity === "error").length === 0;
  const message = isValid ? "Syntax valid" : errors[0].message;

  return {
    isValid,
    errors,
    message,
  };
}

/**
 * Find line number of a pattern in code
 */
function findLineNumber(code: string, pattern: string): number {
  const lines = code.split("\n");
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes(pattern)) {
      return i + 1;
    }
  }
  return 1;
}

/**
 * Extract clock signal from SVA code
 */
export function extractClockSignal(code: string): string {
  const match = code.match(/@\s*\(\s*(?:posedge|negedge)\s+(\w+)\s*\)/);
  return match ? match[1] : "";
}

/**
 * Extract reset signal from SVA code
 */
export function extractResetSignal(code: string): string {
  // Pattern 1: disable iff
  let match = code.match(
    /disable\s+iff\s*\(\s*!?\s*(\w*reset\w*|\w*rst\w*)\s*\)/i
  );
  if (match) return match[1];

  // Pattern 2: if statement
  match = code.match(/if\s*\(\s*!?\s*(\w*reset\w*|\w*rst\w*)\s*\)/i);
  if (match) return match[1];

  return "";
}

/**
 * Extract signals from SVA code
 */
export function extractSignals(code: string): string[] {
  // Remove comments
  let cleanCode = code.replace(/\/\/.*$/gm, "");
  cleanCode = cleanCode.replace(/\/\*[\s\S]*?\*\//g, "");

  // Find all identifiers
  const identifiers = cleanCode.match(/\b[a-zA-Z_][a-zA-Z0-9_]*\b/g) || [];

  // Filter out keywords
  const keywords = new Set([
    "assert",
    "property",
    "assume",
    "cover",
    "posedge",
    "negedge",
    "if",
    "else",
    "disable",
    "iff",
    "and",
    "or",
    "not",
    "throughout",
    "within",
    "intersect",
    "first_match",
    "sequence",
    "endsequence",
    "endproperty",
    "begin",
    "end",
    "module",
    "endmodule",
  ]);

  const signals = identifiers.filter((id) => !keywords.has(id.toLowerCase()));

  // Remove duplicates
  return Array.from(new Set(signals));
}

import { PatentFormat } from '../types';

const USPTO_FIELD_CODES = [
  "IN", "AN", "TTL", "ABST", "SPEC", "ACLM", "CPC", "PN", 
  "APD", "ISD", "PRD", "EXP", "PTY", "LREP", "CRCL" 
  // Add more as needed, these are common ones
];

export function validateQuery(query: string, format: PatentFormat): boolean {
  if (!query.trim()) return true;

  // Basic validation: these regex are simplified and won't catch all syntax errors,
  // especially with complex nested structures.
  // Consider a more robust parsing approach for advanced validation.
  switch (format) {
    case 'google':
      // Allows field:value, "quoted phrases", terms, and AND/OR/NOT.
      // Still basic, doesn't deeply validate parentheses.
      return /^(?:[\w-]+:(?:\S+|"[^"]+")|"[^"]+"|\S+)(?:\s+(?:AND|OR|NOT)\s+(?:[\w-]+:(?:\S+|"[^"]+")|"[^"]+"|\S+))*$/i.test(query);
    
    case 'uspto':
      // Allows FIELD/value, FIELD/(complex value), "quoted phrases", terms, and AND/OR/NOT.
      return /^(?:[A-Z]{2,4}\/(?:[^/\s]+(?:\s[^/\s]+)*|"[^"]+"|\([^)]+\))|"[^"]+"|\S+)(?:\s+(?:AND|OR|NOT)\s+(?:[A-Z]{2,4}\/(?:[^/\s]+(?:\s[^/\s]+)*|"[^"]+"|\([^)]+\))|"[^"]+"|\S+))*$/i.test(query);
    
    case 'unknown':
      return validateQuery(query, 'google') || validateQuery(query, 'uspto');
    
    default:
      return true; 
  }
}

export function correctQuery(query: string, format: PatentFormat): string {
  if (!query.trim()) return query;

  const words = query.split(/\s+/);
  const OPERATORS_GOOGLE = ['AND', 'OR', 'NOT', 'NEAR']; // NEAR/N needs special handling if quoting logic changes
  const OPERATORS_USPTO = ['AND', 'OR', 'NOT', 'ADJ', 'SAME', 'WITH']; // ADJn needs special handling
  
  switch (format) {
    case 'google':
      return words.map(word => {
        if (OPERATORS_GOOGLE.some(op => word.toUpperCase().startsWith(op))) return word; // Handles AND, NEAR, NEAR/5 etc.
        if (word.includes(':')) return word; 
        if (!word.startsWith('"') && !word.endsWith('"')) {
            return `"${word}"`;
        }
        return word;
      }).join(' ');
    
    case 'uspto':
      return words.map(word => {
        if (OPERATORS_USPTO.some(op => word.toUpperCase().startsWith(op))) return word.toUpperCase(); // Handles ADJ, ADJ5, ensures operators are uppercase
        if (word.includes('/')) return word; 
        // Check if it's a known field code that needs a slash
        if (USPTO_FIELD_CODES.includes(word.toUpperCase()) && !word.endsWith('/')) return `${word.toUpperCase()}/`;
        if (!word.startsWith('"') && !word.endsWith('"')) return `"${word}"`;
        return word;
      }).join(' ');
    
    case 'unknown': // Fallback for unknown, attempt to guess and correct
      const detectedFormat = detectBestFormat(query); // New helper function
      if (detectedFormat !== 'unknown') {
        return correctQuery(query, detectedFormat);
      }
      return query; // If still unknown, return as is
    
    default:
      return query;
  }
}

// Helper to be used by correctQuery for 'unknown' case.
// This is a simplified version of what might be in formatDetector.ts
function detectBestFormat(query: string): PatentFormat {
  const googleScore = calculateSimilarityScore(query, 'google');
  const usptoScore = calculateSimilarityScore(query, 'uspto');

  if (googleScore > usptoScore) return 'google';
  if (usptoScore > googleScore) return 'uspto';
  // If scores are equal or both zero, can have a default or keep as unknown
  if (query.includes('cpc/')) return 'google'; // Default if ambiguous
  return 'unknown';
}


function calculateSimilarityScore(query: string, format: PatentFormat): number {
  // Keep existing scoring or refine it.
  // More specific patterns could improve accuracy.
  const patterns: Partial<Record<PatentFormat, RegExp[]>> = {
    google: [
      /\b(?:inventor|assignee|title|abstract|after|before|country|status|type):/gi, // Field prefixes
      /\sNEAR(?:\/\d+)?\s/gi, // NEAR operator
      /"[^"]+"/g // Quoted phrases
    ],
    uspto: [
      /\b(?:AN|IN|TTL|ABST|SPEC|ACLM|CPC|PN|APD|ISD)\//gi, // Field prefixes with /
      /\sADJ(?:\d+)?\s/gi, // ADJ operator
      /\s(?:SAME|WITH)\s/gi, // SAME/WITH operators
      /"[^"]+"/g // Quoted phrases
    ]
  };

  const formatPatterns = patterns[format];
  if (!formatPatterns) return 0;

  let score = 0;
  for (const pattern of formatPatterns) {
    score += (query.match(pattern) || []).length;
  }
  return score;
}
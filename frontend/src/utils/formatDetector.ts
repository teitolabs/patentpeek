import { PatentFormat } from '../types';

export function detectFormat(query: string): PatentFormat {
  const lowerQuery = query.toLowerCase();
  const trimmedQuery = query.trim();

  if (!trimmedQuery) return 'unknown'; // Or a default like 'google'

  // --- Google Patents specific checks ---
  const googleFieldPatterns = [
    /\b(?:inventor|assignee|title|abstract|after|before|priority|filing|publication_date|country|status|type):/i
  ];
  if (/\sNEAR(?:\/\d*)?\s/i.test(query)) return 'google'; // NEAR operator is distinctive
  if (googleFieldPatterns.some(pattern => pattern.test(query))) return 'google';
  

  // --- USPTO specific checks ---
  const usptoFieldPatterns = [
    /\b(?:AN|IN|TTL|ABST|SPEC|ACLM|PN|APD|ISD|PRD|EXP|PTY|LREP|CRCL)\//i // Common USPTO field codes with slash
  ];
  // USPTO operators: ADJ, ADJn, SAME, WITH
  if (/\s(?:ADJ(?:\d*)?|SAME|WITH)\s/i.test(query)) return 'uspto';
  if (usptoFieldPatterns.some(pattern => pattern.test(query))) return 'uspto';
  
  // Legacy USPTO field suffixes like .TI., .AB. (less common in Patent Public Search)
  if (/\.[a-z]{2,4}\./i.test(lowerQuery)) return 'uspto'; 

  // --- Shared or ambiguous checks ---
  // CPC/ is used by both. If it's the only strong signal, it's ambiguous.
  const cpcPattern = /\bCPC\//i; // More specific CPC pattern

  // Score-based detection for ambiguity
  let googleScore = 0;
  let usptoScore = 0;

  if (/\sNEAR(?:\/\d*)?\s/i.test(query)) googleScore += 2;
  googleFieldPatterns.forEach(p => { if (p.test(query)) googleScore++; });

  if (/\s(?:ADJ(?:\d*)?|SAME|WITH)\s/i.test(query)) usptoScore += 2;
  usptoFieldPatterns.forEach(p => { if (p.test(query)) usptoScore++; });
  if (/\.[a-z]{2,4}\./i.test(lowerQuery)) usptoScore++;

  if (cpcPattern.test(query)) {
    // If CPC is present, slightly prefer the one with other indicators
    googleScore += 0.5;
    usptoScore += 0.5;
  }

  if (googleScore > usptoScore) return 'google';
  if (usptoScore > googleScore) return 'uspto';

  // If scores are equal or both low (e.g. just a keyword or only CPC)
  if (cpcPattern.test(query) && googleScore === 0.5 && usptoScore === 0.5) {
    return 'google'; // Default to Google if only CPC/ is found and nothing else.
  }
  
  // Final fallback if no strong indicators or truly ambiguous
  // If query contains quotes, it's common to both.
  // If it's just alphanumeric words, it's also common.
  // A simple keyword "solar panel" is valid in both. Default to Google.
  if (/^[a-zA-Z0-9\s"()*\-$?]+$/.test(trimmedQuery) && googleScore === 0 && usptoScore === 0) {
     // Check for standalone operators without field context - might indicate format
    if (/\b(AND|OR|NOT)\b/.test(query) && !query.includes(':') && !query.includes('/')) {
        // If only general operators and no field specifiers, it's still ambiguous.
        // Google is a reasonable default here too.
        return 'google';
    }
    return 'google'; // Default for simple text queries
  }

  return 'unknown';
}
import { PatentFormat, ConversionResult } from '../types';

// More comprehensive conversion
export function convertQuery(
  query: string,
  fromFormat: PatentFormat,
  toFormat: PatentFormat
): ConversionResult {
  if (fromFormat === toFormat || fromFormat === 'unknown') {
    return { text: query, format: fromFormat === 'unknown' ? 'unknown' : toFormat };
  }

  let convertedText = query;

  if (toFormat === 'google') { // Convert TO Google Patents
    if (fromFormat === 'uspto') {
      convertedText = convertedText
        // Field codes
        .replace(/\bAN\//gi, 'assignee:')
        .replace(/\bIN\//gi, 'inventor:')
        .replace(/\bTTL\//gi, 'title:')
        .replace(/\bABST\//gi, 'abstract:')
        .replace(/\bPN\//gi, '') 
        .replace(/\bSPEC\//gi, '') 
        .replace(/\bACLM\//gi, '') 
        .replace(/\bCPC\//gi, 'cpc/')
        // Operators
        .replace(/\s+ADJ(\d*)\s+/gi, (_match, p1) => ` NEAR/${p1 || 1} `) 
        .replace(/\s+ADJ\s+/gi, ' NEAR/1 ') 
        .replace(/\s+(SAME|WITH)\s+/gi, ' AND '); 
      convertedText = convertedText.replace(/\s\s+/g, ' ').trim();
    }
  } else if (toFormat === 'uspto') { // Convert TO USPTO
    if (fromFormat === 'google') {
      convertedText = convertedText
        // Field codes
        .replace(/\binventor:/gi, 'IN/')
        .replace(/\bassignee:/gi, 'AN/')
        .replace(/\btitle:/gi, 'TTL/')
        .replace(/\babstract:/gi, 'ABST/')
        .replace(/\bcpc:/gi, 'CPC/')
        // Operators
        .replace(/\s+NEAR\/(\d+)\s+/gi, (_match, p1) => {
          const num = parseInt(p1, 10);
          return num === 1 ? ' ADJ ' : ` ADJ${num} `;
        })
        .replace(/\s+NEAR\s+/gi, ' ADJ ') // Handles NEAR without a specified number
        .replace(/\b(AND|OR|NOT)\b/g, (match) => match.toUpperCase());
    }
  }

  return {
    text: convertedText,
    format: toFormat,
  };
}
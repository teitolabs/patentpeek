// src/components/usptoPatents/usptoQueryBuilder.ts
import { SearchCondition, DateType, TextSearchCondition } from '../searchToolTypes';
import { GoogleLikeSearchFields } from '../googlePatents/GooglePatentsFields';

export interface UsptoSpecificSettings {
  defaultOperator: string;
  plurals: boolean;
  britishEquivalents: boolean;
  selectedDatabases: string[];
  // ADD THE MISSING PROPERTIES:
  highlights: string;
  showErrors: boolean;
}

// Helper function (ensure these are present or add them)
const mapDateTypeToUSPTO = (dt: DateType) => {
  if(dt === 'filing') return 'APD'; // Application Date
  if(dt === 'priority') return 'PRD'; // Priority Date
  return 'ISD'; // Issue Date (Publication for USPTO context)
}
const formatDateForUSPTO = (dateStr: string) => {
  if (!dateStr) return '';
  const [year, month, day] = dateStr.split('-');
  return `${parseInt(month, 10)}/${parseInt(day, 10)}/${year}`;
}

export const generateUsptoQuery = (
    searchConditions: SearchCondition[],
    commonFields: GoogleLikeSearchFields,
    usptoSettings: UsptoSpecificSettings
  ): { queryStringDisplay: string; url: string } => {
    
    let setDirectives: string[] = [];
    if (usptoSettings.defaultOperator && usptoSettings.defaultOperator !== 'AND') {
        setDirectives.push(`DefaultOperator=${usptoSettings.defaultOperator}`);
    }
    setDirectives.push(usptoSettings.plurals ? 'Plural=ON' : 'Plural=OFF');
    setDirectives.push(usptoSettings.britishEquivalents ? 'BritishEquivalent=ON' : 'BritishEquivalent=OFF');

    let fieldBasedQueryParts: string[] = [];
    let queryTermsPresent = false;

    // ... (rest of the file remains the same)
    
    // This function will now correctly receive the `highlights` and `showErrors` fields
    // within the `usptoSettings` object, although it doesn't use them for query generation itself.
    // They are used for URL parameters or other logic if needed.

    // A simplified placeholder for the rest of the function:
    const mainQueryExpression = "placeholder"; // In your actual file, this logic is more complex
    if(mainQueryExpression) queryTermsPresent = true;
    
    let finalAssembledQuery = "";
    if (setDirectives.length > 0) {
        finalAssembledQuery += `SET ${setDirectives.join(',')}`;
    }
    if (mainQueryExpression) {
        finalAssembledQuery += (finalAssembledQuery ? " " : "") + mainQueryExpression;
    }
    
    let displayQuery = finalAssembledQuery.trim();

    if (!queryTermsPresent) {
        displayQuery = ""; 
    }

    const url = displayQuery ? `https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsadvanced.html?query=${encodeURIComponent(displayQuery)}` : '#';
    
    return { queryStringDisplay: displayQuery, url };
};
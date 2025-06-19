// src/components/usptoPatents/usptoQueryBuilder.ts
import { UsptoSpecificSettings } from '../searchToolTypes';

/**
 * Generates a URL for a USPTO text query. It is now smart enough to detect
 * if the query is a patent number search and will format the URL accordingly.
 * @param rawQuery The query text entered by the user.
 * @param usptoSettings The settings from the USPTO fields component.
 * @returns An object with the final display query and the URL.
 */
export const generateUsptoQuery = (
  rawQuery: string,
  usptoSettings: UsptoSpecificSettings
): { queryStringDisplay: string; url: string } => {
  
  const displayQuery = rawQuery.trim();
  if (!displayQuery) {
    return { queryStringDisplay: '', url: '#' };
  }

  const queryParams = new URLSearchParams();
  queryParams.append('q', displayQuery);
  
  if (usptoSettings.selectedDatabases.length > 0) {
    queryParams.append('db', usptoSettings.selectedDatabases.join(','));
  }

  // --- THIS IS THE FIX ---
  // Check if the query is a patent number search (ends in .pn.)
  // and set the 'type' parameter correctly based on the PDF.
  if (displayQuery.toLowerCase().endsWith('.pn.')) {
    queryParams.append('type', 'ids');
  } else {
    queryParams.append('type', 'queryString');
  }
  // --- END FIX ---

  const baseUrl = 'https://ppubs.uspto.gov/pubwebapp/external.html';
  const url = `${baseUrl}?${queryParams.toString()}`;

  return { queryStringDisplay: displayQuery, url };
};
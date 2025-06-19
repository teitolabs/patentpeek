// src/components/usptoPatents/usptoQueryBuilder.ts
import { UsptoSpecificSettings } from '../searchToolTypes';

/**
 * Generates a final USPTO query string and URL from the raw query
 * text and specific settings.
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

  // Use URLSearchParams to safely construct the query string
  const queryParams = new URLSearchParams();

  // The 'q' parameter is the user's search query
  queryParams.append('q', displayQuery);

  // The 'db' parameter is a comma-separated list of selected databases
  // If no database is selected, the API defaults to all, so we don't need to add the param
  if (usptoSettings.selectedDatabases.length > 0) {
    queryParams.append('db', usptoSettings.selectedDatabases.join(','));
  }

  // The 'type' parameter should be 'queryString' for text queries
  queryParams.append('type', 'queryString');

  // The base URL for external searches
  const baseUrl = 'https://ppubs.uspto.gov/pubwebapp/external.html';
  const url = `${baseUrl}?${queryParams.toString()}`;

  // The display string is just the user's raw query
  return { queryStringDisplay: displayQuery, url };
};
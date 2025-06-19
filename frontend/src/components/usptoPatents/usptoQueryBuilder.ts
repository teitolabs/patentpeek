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
  
  const mainQueryExpression = rawQuery.trim();
  const queryTermsPresent = !!mainQueryExpression;

  // For the USPTO web interface, SET directives are not used in the URL.
  // The query is simply the text entered by the user.
  let displayQuery = mainQueryExpression;

  if (!queryTermsPresent) {
    displayQuery = "";
  }

  // Construct the final URL for USPTO Public Search.
  // The database selection is part of the URL parameters.
  const databases = usptoSettings.selectedDatabases.join(',');
  const url = displayQuery
    ? `https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsadvanced.html?query=${encodeURIComponent(displayQuery)}&db=${databases}`
    : '#';

  return { queryStringDisplay: displayQuery, url };
};
// src/components/googlePatents/googleApi.ts
import { PatentFormat } from '../../types';
import { SearchCondition, TextSearchCondition, SearchToolType, GoogleLikeSearchFields } from '../searchToolTypes';
import { UsptoSpecificSettings } from '../usptoPatents/usptoQueryBuilder';

// --- START: Define Payload-Specific Types ---
interface TextSearchDataPayload {
  type: "TEXT";
  text: string;
}

interface SearchConditionPayload {
  id: string;
  type: SearchToolType;
  data: TextSearchDataPayload;
}
// --- END: Payload-Specific Types ---


export interface GenerateResponse {
  queryStringDisplay: string;
  url: string;
  ast: Record<string, any> | null; // <-- ADDED
}

export interface ParseResponse {
  searchConditions: SearchCondition[];
  googleLikeFields: GoogleLikeSearchFields;
  usptoSpecificSettings: UsptoSpecificSettings;
}

export interface ConvertResponse {
  converted_text: string | null;
  error: string | null;
  settings: Record<string, any>;
}

/**
 * Sends structured state to the backend to generate a query string.
 */
export const generateQuery = async (
  format: PatentFormat,
  searchConditions: SearchCondition[],
  googleLikeFields: GoogleLikeSearchFields,
  usptoSpecificSettings: UsptoSpecificSettings,
): Promise<GenerateResponse> => {
  const processedSearchConditions: SearchConditionPayload[] = searchConditions.map(condition => {
      const textData = condition.data as TextSearchCondition['data'];
      return {
        id: condition.id,
        type: 'TEXT',
        data: {
          type: 'TEXT',
          text: textData.text,
        }
      };
  });

  try {
    const response = await fetch('/api/generate-query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format, searchConditions: processedSearchConditions, googleLikeFields, usptoSpecificSettings }),
    });
    const result = await response.json();
    if (!response.ok) {
      const errorMessage = result.detail ? JSON.stringify(result.detail) : (result.error || 'Error from server');
      return { queryStringDisplay: `Validation Error: ${errorMessage}`, url: '#', ast: null };
    }
    return result;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Network error.";
    return { queryStringDisplay: `API Error: ${errorMessage}`, url: "#", ast: null };
  }
};

/**
 * Sends a raw query string to the backend to be parsed into structured state.
 */
export const parseQuery = async (
  format: PatentFormat,
  queryString: string
): Promise<ParseResponse> => {
  try {
    const response = await fetch('/api/parse-query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format, queryString }),
    });
    const result = await response.json();
    if (!response.ok) {
        throw new Error(result.detail || result.error || 'Error from server');
    }
    return result;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Network error.";
    throw new Error(`API Error: ${errorMessage}`);
  }
};

/**
 * Sends a query to be converted from one format to another.
 */
export const convertQuery = async (
  query_string: string,
  source_format: PatentFormat,
  target_format: PatentFormat,
): Promise<ConvertResponse> => {
    const response = await fetch('/api/convert-query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query_string, source_format, target_format })
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({error: 'Conversion failed with network error.'}));
        throw new Error(errorData.error);
    }
    return response.json();
}
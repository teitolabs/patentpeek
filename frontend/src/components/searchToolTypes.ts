// src/components/searchToolTypes.ts
export type DateType = 'priority' | 'filing' | 'publication';
export type PatentOffice =
  | 'US' | 'EP' | 'WO' | 'JP' | 'CN' | 'KR' | 'DE' | 'GB' | 'FR' | 'CA'
  | 'AE' | 'AG' | 'AL' | 'AM' | 'AO' | 'AP' | 'AR' | 'AT' | 'AU' | 'AW'
  | 'AZ' | 'BA' | 'BB' | 'BD' | 'BE' | 'BF' | 'BG' | 'BH' | 'BJ' | 'BN'
  | 'BO' | 'BR' | 'BW' | 'BX' | 'BY' | 'BZ' | 'CF' | 'CG' | 'CH' | 'CI'
  | 'CL' | 'CM' | 'CO' | 'CR' | 'CS' | 'CU' | 'CY' | 'CZ' | 'DD' | 'DJ'
  | 'DK' | 'DM' | 'DO' | 'DZ' | 'EA' | 'EC' | 'EE' | 'EG' | 'EM' | 'ES'
  | 'FI' | 'GA' | 'GC' | 'GD' | 'GE' | 'GH' | 'GM' | 'GN' | 'GQ' | 'GR'
  | 'GT' | 'GW' | 'HK' | 'HN' | 'HR' | 'HU' | 'IB' | 'ID' | 'IE' | 'IL'
  | 'IN' | 'IR' | 'IS' | 'IT' | 'JO' | 'KE' | 'KG' | 'KH' | 'KM' | 'KN'
  | 'KP' | 'KW' | 'KZ' | 'LA' | 'LC' | 'LI' | 'LK' | 'LR' | 'LS' | 'LT'
  | 'LU' | 'LV' | 'LY' | 'MA' | 'MC' | 'MD' | 'ME' | 'MG' | 'MK' | 'ML'
  | 'MN' | 'MO' | 'MR' | 'MT' | 'MW' | 'MX' | 'MY' | 'MZ' | 'NA' | 'NE'
  | 'NG' | 'NI' | 'NL' | 'NO' | 'OA' | 'OM' | 'PA' | 'PE' | 'PG' | 'PH'
  | 'PL' | 'PT' | 'PY' | 'QA' | 'RO' | 'RS' | 'RU' | 'RW' | 'SA' | 'SC'
  | 'SD' | 'SE' | 'SG' | 'SI' | 'SK' | 'SL' | 'SM' | 'SN' | 'ST' | 'SU'
  | 'SV' | 'SY' | 'SZ' | 'TD' | 'TG' | 'TH' | 'TJ' | 'TM' | 'TN' | 'TR'
  | 'TT' | 'TW' | 'TZ' | 'UA' | 'UG' | 'UY' | 'UZ' | 'VC' | 'VE' | 'VN'
  | 'YU' | 'ZA' | 'ZM' | 'ZW' | 'OTHER' | '';

export type Language =
  | 'ENGLISH' | 'GERMAN' | 'CHINESE' | 'FRENCH' | 'SPANISH' | 'ARABIC'
  | 'JAPANESE' | 'KOREAN' | 'PORTUGUESE' | 'RUSSIAN' | 'ITALIAN' | 'DUTCH'
  | 'SWEDISH' | 'FINNISH' | 'NORWEGIAN' | 'DANISH' | '';

export type PatentStatus = 'GRANT' | 'APPLICATION' | '';
export type PatentType = 'PATENT' | 'DESIGN' | 'PLANT' | 'REISSUE' | 'SIR' | 'UTILITY' | 'PROVISIONAL' | 'DEFENSIVE_PUBLICATION' | 'STATUTORY_INVENTION_REGISTRATION' | 'OTHER' | '';
export type LitigationStatus = 'YES' | 'NO' | '';

// The only active search tool type is TEXT.
export type SearchToolType = 'TEXT';

export interface BaseSearchCondition {
  id: string;
  type: SearchToolType;
}

// Simplified data structure for a text search condition.
// Scopes and term operators have been removed as they are no longer used.
export interface InternalTextSearchData {
  text: string;
  error?: string | null;
}

export interface TextSearchCondition extends BaseSearchCondition {
  type: 'TEXT';
  data: InternalTextSearchData;
}

// The SearchCondition is now only ever a TextSearchCondition.
export type SearchCondition = TextSearchCondition;

// This payload is kept for clarity but is now simpler.
export interface BackendSearchConditionPayload {
  id: string;
  type: SearchToolType;
  data: {
    text: string;
  };
}
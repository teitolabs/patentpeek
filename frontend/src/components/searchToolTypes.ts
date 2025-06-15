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
export type SearchToolType = 'TEXT';

export interface DynamicEntry {
  id: string;
  value: string;
}

export interface GoogleLikeSearchFields {
  dateFrom: string;
  dateTo: string;
  dateType: DateType;
  inventors: DynamicEntry[];
  assignees: DynamicEntry[];
  patentOffices: PatentOffice[];
  languages: Language[];
  status: PatentStatus;
  patentType: PatentType;
  litigation: LitigationStatus;
}

// --- THIS IS THE CRITICAL FIX ---
// We are moving this interface here to be a shared, central type definition.
// This version is also complete, matching the backend model.
export interface UsptoSpecificSettings {
  defaultOperator: string;
  plurals: boolean;
  britishEquivalents: boolean;
  selectedDatabases: string[];
  highlights: string;
  showErrors: boolean;
}

export interface BaseSearchCondition { id: string; type: SearchToolType; }
export interface InternalTextSearchData {
  text: string;
  error?: string | null;
}
export interface TextSearchCondition extends BaseSearchCondition { type: 'TEXT'; data: InternalTextSearchData; }
export type SearchCondition = TextSearchCondition;

export interface BackendSearchConditionPayload {
  id: string;
  type: SearchToolType;
  data: {
    text: string;
  };
}
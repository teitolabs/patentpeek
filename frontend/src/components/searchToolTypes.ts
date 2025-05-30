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
export type QueryScope = 'TI' | 'AB' | 'CL' | 'CPC' | 'FT';
export type TermOperator = 'ALL' | 'EXACT' | 'ANY' | 'NONE';
export type SearchToolType = 'TEXT' | 'CLASSIFICATION' | 'CHEMISTRY' | 'MEASURE' | 'NUMBERS';
export type LitigationStatus = 'YES' | 'NO' | '';

export interface BaseSearchCondition { id: string; type: SearchToolType; }
export interface InternalTextSearchData { text: string; selectedScopes: Set<QueryScope>; termOperator: TermOperator; }
export interface TextSearchCondition extends BaseSearchCondition { type: 'TEXT'; data: InternalTextSearchData; }
export interface ClassificationSearchData { cpc: string; option: 'CHILDREN' | 'EXACT'; }
export interface ClassificationSearchCondition extends BaseSearchCondition { type: 'CLASSIFICATION'; data: ClassificationSearchData; }

export type ChemistryOperator = 'EXACT' | 'SIMILAR' | 'SUBSTRUCTURE' | 'SMARTS';
export type ChemistryUiOperatorLabel = 'Exact' | 'Exact Batch' | 'Similar' | 'Substructure' | 'Substructure (SMARTS)';
export type ChemistryDocScope = 'FULL' | 'CLAIMS_ONLY';
export interface ChemistrySearchData { term: string; operator: ChemistryOperator; uiOperatorLabel: ChemistryUiOperatorLabel; docScope: ChemistryDocScope; }
export interface ChemistrySearchCondition extends BaseSearchCondition { type: 'CHEMISTRY'; data: ChemistrySearchData; }

export interface MeasureSearchData { measurements: string; units_concepts: string; }
export interface MeasureSearchCondition extends BaseSearchCondition { type: 'MEASURE'; data: MeasureSearchData; }

export type DocumentNumberType = 'APPLICATION' | 'PUBLICATION' | 'EITHER';
export interface NumbersSearchData {
  doc_ids_text: string;
  number_type: DocumentNumberType;
  country_restriction: string;
  preferred_countries_order: string;
}
export interface NumbersSearchCondition extends BaseSearchCondition { type: 'NUMBERS'; data: NumbersSearchData; }

export type SearchCondition =
  | TextSearchCondition
  | ClassificationSearchCondition
  | ChemistrySearchCondition
  | MeasureSearchCondition
  | NumbersSearchCondition;

export interface BackendSearchConditionPayload {
  id: string;
  type: SearchToolType;
  data: any;
}

// This type is Google-specific, so it will be defined in GooglePatentsFields.tsx
// export interface GoogleLikeSearchFields { ... }
import React, { useState, useEffect, useRef } from 'react';
import { PatentFormat } from '../types';
import { 
    Building2, XCircle, CalendarDays, ChevronDown, Users, Briefcase, Filter, 
    Settings2, Type as TypeIcon, Wand2, Link as LinkIcon, ShieldQuestion, Globe, Check, Languages // Added Check, Languages, renamed Type to TypeIcon
} from 'lucide-react';
import SearchToolModal, { ModalToolData } from './SearchToolModal';

// --- Type Definitions ---
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

// Expanded Language type
export type Language =
  | 'ENGLISH' | 'GERMAN' | 'CHINESE' | 'FRENCH' | 'SPANISH' | 'ARABIC'
  | 'JAPANESE' | 'KOREAN' | 'PORTUGUESE' | 'RUSSIAN' | 'ITALIAN' | 'DUTCH'
  | 'SWEDISH' | 'FINNISH' | 'NORWEGIAN' | 'DANISH' | ''; // Empty for 'Any'

export type PatentStatus = 'GRANT' | 'APPLICATION' | '';
export type PatentType = 'PATENT' | 'DESIGN' | 'PLANT' | 'REISSUE' | 'SIR' | 'UTILITY' | 'PROVISIONAL' | 'DEFENSIVE_PUBLICATION' | 'STATUTORY_INVENTION_REGISTRATION' | 'OTHER' | '';
export type QueryScope = 'TI' | 'AB' | 'CL' | 'CPC' | 'FT';
export type TermOperator = 'ALL' | 'EXACT' | 'ANY' | 'NONE';
export type SearchToolType = 'TEXT' | 'CLASSIFICATION' | 'CHEMISTRY' | 'MEASURE' | 'NUMBERS';
export type LitigationStatus = 'YES' | 'NO' | '';

// ... (BaseSearchCondition, InternalTextSearchData, etc. remain the same) ...
export interface BaseSearchCondition { id: string; type: SearchToolType; }
export interface InternalTextSearchData { text: string; selectedScopes: Set<QueryScope>; termOperator: TermOperator; }
export interface TextSearchCondition extends BaseSearchCondition { type: 'TEXT'; data: InternalTextSearchData; }
export interface ClassificationSearchData { cpc: string; option: 'CHILDREN' | 'EXACT'; }
export interface ClassificationSearchCondition extends BaseSearchCondition { type: 'CLASSIFICATION'; data: ClassificationSearchData; }
interface GenericSearchConditionData { [key: string]: any; }
interface GenericSearchCondition extends BaseSearchCondition { type: Exclude<SearchToolType, 'TEXT' | 'CLASSIFICATION'>; data: GenericSearchConditionData; }
export type SearchCondition = TextSearchCondition | ClassificationSearchCondition | GenericSearchCondition;

export interface BackendSearchConditionPayload {
  id: string;
  type: SearchToolType;
  data: any;
}


export interface GoogleLikeSearchFields {
  dateFrom: string; dateTo: string; dateType: DateType;
  inventors: Array<{ id: string; value: string }>;
  assignees: Array<{ id: string; value: string }>;
  patentOffices: PatentOffice[]; 
  languages: Language[]; // CHANGED
  status: PatentStatus; patentType: PatentType;
  litigation: LitigationStatus;
  cpc?: string; 
  specificTitle?: string; documentId?: string;
}
export interface ChatInputProps { value: string; activeFormat: PatentFormat; onTabChange: (newFormat: PatentFormat) => void; onMainInputChange: (text: string) => void; }

// --- Options Arrays ---
const dateTypeOptions: Array<{value: DateType; label: string}> = [
    {value: 'publication', label: 'Publication'}, {value: 'priority', label: 'Priority'}, {value: 'filing', label: 'Filing'},
];

// Patent Office options - using code as label, maintaining specified order
const patentOfficeOptions: Array<{value: PatentOffice; label: string}> = [
    {value: 'WO', label: 'WO'}, {value: 'US', label: 'US'}, {value: 'EP', label: 'EP'}, 
    {value: 'JP', label: 'JP'}, {value: 'KR', label: 'KR'}, {value: 'CN', label: 'CN'},
    {value: 'AE', label: 'AE'}, {value: 'AG', label: 'AG'}, {value: 'AL', label: 'AL'},
    {value: 'AM', label: 'AM'}, {value: 'AO', label: 'AO'}, {value: 'AP', label: 'AP'},
    {value: 'AR', label: 'AR'}, {value: 'AT', label: 'AT'}, {value: 'AU', label: 'AU'},
    {value: 'AW', label: 'AW'}, {value: 'AZ', label: 'AZ'}, {value: 'BA', label: 'BA'},
    {value: 'BB', label: 'BB'}, {value: 'BD', label: 'BD'}, {value: 'BE', label: 'BE'},
    {value: 'BF', label: 'BF'}, {value: 'BG', label: 'BG'}, {value: 'BH', label: 'BH'},
    {value: 'BJ', label: 'BJ'}, {value: 'BN', label: 'BN'}, {value: 'BO', label: 'BO'},
    {value: 'BR', label: 'BR'}, {value: 'BW', label: 'BW'}, {value: 'BX', label: 'BX'},
    {value: 'BY', label: 'BY'}, {value: 'BZ', label: 'BZ'}, {value: 'CA', label: 'CA'}, // Moved CA to maintain original block
    {value: 'CF', label: 'CF'}, {value: 'CG', label: 'CG'}, {value: 'CH', label: 'CH'},
    {value: 'CI', label: 'CI'}, {value: 'CL', label: 'CL'}, {value: 'CM', label: 'CM'},
    {value: 'CO', label: 'CO'}, {value: 'CR', label: 'CR'}, {value: 'CS', label: 'CS'},
    {value: 'CU', label: 'CU'}, {value: 'CY', label: 'CY'}, {value: 'CZ', label: 'CZ'},
    {value: 'DD', label: 'DD'}, {value: 'DE', label: 'DE'}, // Moved DE
    {value: 'DJ', label: 'DJ'}, {value: 'DK', label: 'DK'}, {value: 'DM', label: 'DM'},
    {value: 'DO', label: 'DO'}, {value: 'DZ', label: 'DZ'}, {value: 'EA', label: 'EA'},
    {value: 'EC', label: 'EC'}, {value: 'EE', label: 'EE'}, {value: 'EG', label: 'EG'},
    {value: 'EM', label: 'EM'}, {value: 'ES', label: 'ES'}, {value: 'FI', label: 'FI'},
    {value: 'FR', label: 'FR'}, // Moved FR
    {value: 'GA', label: 'GA'}, {value: 'GB', label: 'GB'}, // Moved GB
    {value: 'GC', label: 'GC'}, {value: 'GD', label: 'GD'}, {value: 'GE', label: 'GE'},
    {value: 'GH', label: 'GH'}, {value: 'GM', label: 'GM'}, {value: 'GN', label: 'GN'},
    {value: 'GQ', label: 'GQ'}, {value: 'GR', label: 'GR'}, {value: 'GT', label: 'GT'},
    {value: 'GW', label: 'GW'}, {value: 'HK', label: 'HK'}, {value: 'HN', label: 'HN'},
    {value: 'HR', label: 'HR'}, {value: 'HU', label: 'HU'}, {value: 'IB', label: 'IB'},
    {value: 'ID', label: 'ID'}, {value: 'IE', label: 'IE'}, {value: 'IL', label: 'IL'},
    {value: 'IN', label: 'IN'}, {value: 'IR', label: 'IR'}, {value: 'IS', label: 'IS'},
    {value: 'IT', label: 'IT'}, {value: 'JO', label: 'JO'}, {value: 'KE', label: 'KE'},
    {value: 'KG', label: 'KG'}, {value: 'KH', label: 'KH'}, {value: 'KM', label: 'KM'},
    {value: 'KN', label: 'KN'}, {value: 'KP', label: 'KP'}, {value: 'KW', label: 'KW'},
    {value: 'KZ', label: 'KZ'}, {value: 'LA', label: 'LA'}, {value: 'LC', label: 'LC'},
    {value: 'LI', label: 'LI'}, {value: 'LK', label: 'LK'}, {value: 'LR', label: 'LR'},
    {value: 'LS', label: 'LS'}, {value: 'LT', label: 'LT'}, {value: 'LU', label: 'LU'},
    {value: 'LV', label: 'LV'}, {value: 'LY', label: 'LY'}, {value: 'MA', label: 'MA'},
    {value: 'MC', label: 'MC'}, {value: 'MD', label: 'MD'}, {value: 'ME', label: 'ME'},
    {value: 'MG', label: 'MG'}, {value: 'MK', label: 'MK'}, {value: 'ML', label: 'ML'},
    {value: 'MN', label: 'MN'}, {value: 'MO', label: 'MO'}, {value: 'MR', label: 'MR'},
    {value: 'MT', label: 'MT'}, {value: 'MW', label: 'MW'}, {value: 'MX', label: 'MX'},
    {value: 'MY', label: 'MY'}, {value: 'MZ', label: 'MZ'}, {value: 'NA', label: 'NA'},
    {value: 'NE', label: 'NE'}, {value: 'NG', label: 'NG'}, {value: 'NI', label: 'NI'},
    {value: 'NL', label: 'NL'}, {value: 'NO', label: 'NO'}, {value: 'OA', label: 'OA'},
    {value: 'OM', label: 'OM'}, {value: 'PA', label: 'PA'}, {value: 'PE', label: 'PE'},
    {value: 'PG', label: 'PG'}, {value: 'PH', label: 'PH'}, {value: 'PL', label: 'PL'},
    {value: 'PT', label: 'PT'}, {value: 'PY', label: 'PY'}, {value: 'QA', label: 'QA'},
    {value: 'RO', label: 'RO'}, {value: 'RS', label: 'RS'}, {value: 'RU', label: 'RU'},
    {value: 'RW', label: 'RW'}, {value: 'SA', label: 'SA'}, {value: 'SC', label: 'SC'},
    {value: 'SD', label: 'SD'}, {value: 'SE', label: 'SE'}, {value: 'SG', label: 'SG'},
    {value: 'SI', label: 'SI'}, {value: 'SK', label: 'SK'}, {value: 'SL', label: 'SL'},
    {value: 'SM', label: 'SM'}, {value: 'SN', label: 'SN'}, {value: 'ST', label: 'ST'},
    {value: 'SU', label: 'SU'}, {value: 'SV', label: 'SV'}, {value: 'SY', label: 'SY'},
    {value: 'SZ', label: 'SZ'}, {value: 'TD', label: 'TD'}, {value: 'TG', label: 'TG'},
    {value: 'TH', label: 'TH'}, {value: 'TJ', label: 'TJ'}, {value: 'TM', label: 'TM'},
    {value: 'TN', label: 'TN'}, {value: 'TR', label: 'TR'}, {value: 'TT', label: 'TT'},
    {value: 'TW', label: 'TW'}, {value: 'TZ', label: 'TZ'}, {value: 'UA', label: 'UA'},
    {value: 'UG', label: 'UG'}, {value: 'UY', label: 'UY'}, {value: 'UZ', label: 'UZ'},
    {value: 'VC', label: 'VC'}, {value: 'VE', label: 'VE'}, {value: 'VN', label: 'VN'},
    {value: 'YU', label: 'YU'}, {value: 'ZA', label: 'ZA'}, {value: 'ZM', label: 'ZM'},
    {value: 'ZW', label: 'ZW'}
    // 'OTHER' is not a selectable code, it implies user types it in a query directly
];

const languageOptions: Array<{value: Language; label: string}> = [
    // {value: '', label: 'Any Language'}, // "Any" is an empty array
    {value: 'ENGLISH', label: 'English'}, {value: 'GERMAN', label: 'German'},
    {value: 'CHINESE', label: 'Chinese'}, {value: 'FRENCH', label: 'French'},
    {value: 'SPANISH', label: 'Spanish'}, {value: 'ARABIC', label: 'Arabic'},
    {value: 'JAPANESE', label: 'Japanese'}, {value: 'KOREAN', label: 'Korean'},
    {value: 'PORTUGUESE', label: 'Portuguese'}, {value: 'RUSSIAN', label: 'Russian'},
    {value: 'ITALIAN', label: 'Italian'}, {value: 'DUTCH', label: 'Dutch'},
    {value: 'SWEDISH', label: 'Swedish'}, {value: 'FINNISH', label: 'Finnish'},
    {value: 'NORWEGIAN', label: 'Norwegian'}, {value: 'DANISH', label: 'Danish'}
];

const patentStatusOptions: Array<{value: PatentStatus; label: string}> = [ {value: '', label: 'Any Status'}, {value: 'GRANT', label: 'Grant'}, {value: 'APPLICATION', label: 'Application'}, ];
const patentTypeOptions: Array<{value: PatentType; label: string}> = [
    {value: '', label: 'Any Type'},
    {value: 'PATENT', label: 'Patent (General/Utility)'}, {value: 'UTILITY', label: 'Utility (Explicit)'},
    {value: 'DESIGN', label: 'Design'}, {value: 'PLANT', label: 'Plant'},
    {value: 'REISSUE', label: 'Reissue'}, {value: 'PROVISIONAL', label: 'Provisional'},
    {value: 'DEFENSIVE_PUBLICATION', label: 'Defensive Publication'},
    {value: 'STATUTORY_INVENTION_REGISTRATION', label: 'Statutory Invention Registration (SIR)'},
    {value: 'OTHER', label: 'Other'},
];
const litigationStatusOptions: Array<{value: LitigationStatus; label: string}> = [
    {value: '', label: 'Any Litigation'}, {value: 'YES', label: 'Has Related Litigation'}, {value: 'NO', label: 'No Known Litigation'},
];

// --- Top-Level Helper Components ---
function GoogleGIcon(): React.ReactElement { /* ... same ... */ 
  return (<svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M12.2446 10.925L12.2446 14.005L18.7746 14.005C18.5346 15.095 18.0546 16.125 17.3446 16.965C16.5846 17.855 15.2746 18.665 13.4846 18.665C10.6846 18.665 8.31462 16.375 8.31462 13.495C8.31462 10.615 10.6846 8.32502 13.4846 8.32502C14.9346 8.32502 16.0046 8.92502 16.9546 9.81502L19.1146 7.71502C17.6746 6.38502 15.8046 5.32502 13.4846 5.32502C9.86462 5.32502 6.91462 8.22502 6.91462 11.995C6.91462 15.765 9.86462 18.665 13.4846 18.665C15.9146 18.665 17.7246 17.835 19.0646 16.415C20.4746 14.925 20.9846 12.925 20.9846 11.495C20.9846 10.925 20.9446 10.475 20.8546 10.005L13.4846 10.005L12.2446 10.925Z" /></svg>);
}
function getDateTypeLabel(value: DateType): string { /* ... same ... */ 
    return dateTypeOptions.find(opt => opt.value === value)?.label || 'Select Type';
}
function getLitigationStatusLabel(value: LitigationStatus): string { /* ... same ... */ 
    return litigationStatusOptions.find(opt => opt.value === value)?.label || 'Any Litigation';
}
function getConditionTypeIcon(type: SearchToolType): React.ReactElement { /* ... same ... */ 
    switch(type) {
        case 'TEXT': return <TypeIcon size={18} className="text-gray-600" />;
        case 'CLASSIFICATION': return <Filter size={18} className="text-gray-600" />;
        default: return <Settings2 size={18} className="text-gray-600" />;
    }
}

const formatTabs: Array<{ value: PatentFormat; label: string; icon: React.ReactNode }> = [
  { value: 'google', label: 'Google Patents', icon: <GoogleGIcon /> },
  { value: 'uspto', label: 'USPTO', icon: <Building2 className="h-5 w-5 mr-2" /> },
];

const ChatInput: React.FC<ChatInputProps> = ({
  value: mainQueryValue, activeFormat, onTabChange, onMainInputChange,
}) => {
  const createDefaultTextCondition = (): TextSearchCondition => ({ /* ... same ... */ 
    id: crypto.randomUUID(),
    type: 'TEXT',
    data: { text: '', selectedScopes: new Set(['FT']), termOperator: 'ALL' }
  });

  const [searchConditions, setSearchConditions] = useState<SearchCondition[]>([createDefaultTextCondition()]);
  const [googleLikeFields, setGoogleLikeFields] = useState<GoogleLikeSearchFields>({
    dateFrom: '', dateTo: '', dateType: 'publication',
    inventors: [], assignees: [],
    patentOffices: [], 
    languages: [], // CHANGED
    status: '', patentType: '',
    litigation: '',
    cpc: '', specificTitle: '', documentId: ''
  });
  // ... (other state: currentInventorInput, etc.) ...
  const [currentInventorInput, setCurrentInventorInput] = useState('');
  const [currentAssigneeInput, setCurrentAssigneeInput] = useState('');
  const inventorInputRef = useRef<HTMLInputElement>(null);
  const assigneeInputRef = useRef<HTMLInputElement>(null);
  const [isSearchToolModalOpen, setIsSearchToolModalOpen] = useState(false);
  const [editingCondition, setEditingCondition] = useState<SearchCondition | undefined>(undefined);
  const [queryLinkHref, setQueryLinkHref] = useState<string>('#');
  
  // State for custom dropdowns
  const [isPatentOfficeDropdownOpen, setIsPatentOfficeDropdownOpen] = useState(false);
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
  const patentOfficeRef = useRef<HTMLDivElement>(null);
  const languageRef = useRef<HTMLDivElement>(null);

  // Click outside handlers for custom dropdowns
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (patentOfficeRef.current && !patentOfficeRef.current.contains(event.target as Node)) {
        setIsPatentOfficeDropdownOpen(false);
      }
      if (languageRef.current && !languageRef.current.contains(event.target as Node)) {
        setIsLanguageDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);


  const handleMainQueryDirectInputChange = (e: React.ChangeEvent<HTMLInputElement>) => onMainInputChange(e.target.value);
  const handleTabClick = (newFormat: PatentFormat) => { if (newFormat !== activeFormat) onTabChange(newFormat); };
  const handleOpenSearchToolModal = (conditionToEdit: SearchCondition) => { /* ... same ... */ 
    setEditingCondition(conditionToEdit);
    setIsSearchToolModalOpen(true);
  };
  const handleCloseSearchToolModal = () => { /* ... same ... */ 
    setIsSearchToolModalOpen(false);
    setEditingCondition(undefined);
  };
  const handleUpdateSearchConditionFromModal = (conditionId: string, newType: SearchToolType, newData: ModalToolData) => { /* ... same ... */ 
    setSearchConditions(prev =>
      prev.map(sc => {
        if (sc.id === conditionId) {
          if (newType === 'TEXT') return { ...sc, type: 'TEXT', data: newData as InternalTextSearchData };
          if (newType === 'CLASSIFICATION') return { ...sc, type: 'CLASSIFICATION', data: newData as ClassificationSearchData };
          return { ...sc, type: newType, data: newData };
        }
        return sc;
      })
    );
    handleCloseSearchToolModal();
  };
  const removeSearchCondition = (id: string) => { /* ... same ... */ 
    setSearchConditions(prev => {
        let newConditions = prev.filter(sc => sc.id !== id);
        if (newConditions.length === 0) {
            newConditions = [createDefaultTextCondition()];
        } else {
            const lastCondition = newConditions[newConditions.length - 1];
            const lastIsFilledText = lastCondition.type === 'TEXT' && (lastCondition.data as InternalTextSearchData).text.trim() !== '';
            const lastIsNonText = lastCondition.type !== 'TEXT';
            if (lastIsFilledText || lastIsNonText) {
                newConditions.push(createDefaultTextCondition());
            }
        }
        return newConditions;
    });
  };
  const updateSearchConditionText = (id: string, newText: string) => { /* ... same ... */ 
    setSearchConditions(prevConditions => {
      let updatedConditions = prevConditions.map(sc =>
        (sc.id === id && sc.type === 'TEXT') ? { ...sc, data: { ...(sc.data as InternalTextSearchData), text: newText } } : sc
      );
      const conditionIndex = updatedConditions.findIndex(sc => sc.id === id);
      if (conditionIndex === -1) return updatedConditions;
      const currentCondition = updatedConditions[conditionIndex];
      const isCurrentTextFilled = currentCondition.type === 'TEXT' && (currentCondition.data as InternalTextSearchData).text.trim() !== '';
      const isCurrentTextEmpty = currentCondition.type === 'TEXT' && (currentCondition.data as InternalTextSearchData).text.trim() === '';
      if (isCurrentTextFilled && conditionIndex === updatedConditions.length - 1) {
        updatedConditions.push(createDefaultTextCondition());
      }
      else if (isCurrentTextEmpty && updatedConditions.length > 1 && conditionIndex < updatedConditions.length - 1) {
         updatedConditions.splice(conditionIndex, 1);
      }
      if (updatedConditions.length === 0) {
        updatedConditions = [createDefaultTextCondition()];
      }
      return updatedConditions;
    });
  };
  const handleGoogleLikeFieldChange = <K extends keyof GoogleLikeSearchFields>(field: K, value: GoogleLikeSearchFields[K]) => { /* ... same ... */ 
    setGoogleLikeFields(prev => ({ ...prev, [field]: value }));
  };

  const handlePatentOfficeToggle = (officeCode: PatentOffice) => {
    setGoogleLikeFields(prev => {
      const newPatentOffices = prev.patentOffices.includes(officeCode)
        ? prev.patentOffices.filter(po => po !== officeCode)
        : [...prev.patentOffices, officeCode];
      return { ...prev, patentOffices: newPatentOffices };
    });
  };

  const handleLanguageToggle = (langCode: Language) => {
    setGoogleLikeFields(prev => {
        const newLanguages = prev.languages.includes(langCode)
        ? prev.languages.filter(lang => lang !== langCode)
        : [...prev.languages, langCode];
        return {...prev, languages: newLanguages};
    });
  };

  const addDynamicFieldEntry = (field: 'inventors' | 'assignees') => { /* ... same ... */ 
    const currentInput = field === 'inventors' ? currentInventorInput : currentAssigneeInput;
    const setCurrentInput = field === 'inventors' ? setCurrentInventorInput : setCurrentAssigneeInput;
    const inputRef = field === 'inventors' ? inventorInputRef : assigneeInputRef;
    if (currentInput.trim()) {
      setGoogleLikeFields(prev => ({...prev, [field]: [...prev[field], { id: crypto.randomUUID(), value: currentInput.trim() }]}));
      setCurrentInput(''); inputRef.current?.focus();
    }
  };
  const removeDynamicFieldEntry = (field: 'inventors' | 'assignees', id: string) => { /* ... same ... */ 
    setGoogleLikeFields(prev => ({...prev, [field]: prev[field].filter(entry => entry.id !== id)}));
  };

  const fetchGoogleQueryDetailsFromServer = async (
    currentSearchConditions: SearchCondition[],
    currentGoogleFields: GoogleLikeSearchFields
  ): Promise<{ queryStringDisplay: string; url: string }> => { /* ... same, but ensure patent_offices and languages are passed ... */ 
    const search_conditions_payload: BackendSearchConditionPayload[] = currentSearchConditions
      .map(condition => {
        if (condition.type === 'TEXT' && !(condition.data as InternalTextSearchData).text.trim()) { return null; }
        let conditionData = condition.data;
        if (condition.type === 'TEXT') {
          const textData = condition.data as InternalTextSearchData;
          conditionData = { ...textData, selectedScopes: Array.from(textData.selectedScopes) };
        }
        return { id: condition.id, type: condition.type, data: conditionData };
      })
      .filter(Boolean) as BackendSearchConditionPayload[];

    const payload = {
      structured_search_conditions: search_conditions_payload.length > 0 ? search_conditions_payload : null,
      inventors: currentGoogleFields.inventors.length > 0 ? currentGoogleFields.inventors.map(inv => inv.value) : null,
      assignees: currentGoogleFields.assignees.length > 0 ? currentGoogleFields.assignees.map(asg => asg.value) : null,
      after_date: currentGoogleFields.dateFrom || null,
      after_date_type: currentGoogleFields.dateFrom ? currentGoogleFields.dateType : null,
      before_date: currentGoogleFields.dateTo || null,
      before_date_type: currentGoogleFields.dateTo ? currentGoogleFields.dateType : null,
      patent_offices: currentGoogleFields.patentOffices.length > 0 ? currentGoogleFields.patentOffices : null, 
      languages: currentGoogleFields.languages.length > 0 ? currentGoogleFields.languages : null, // CHANGED
      status: currentGoogleFields.status || null,
      patent_type: currentGoogleFields.patentType || null,
      litigation: currentGoogleFields.litigation || null,
      dedicated_cpc: currentGoogleFields.cpc?.trim() || null,
      dedicated_title: currentGoogleFields.specificTitle?.trim() || null,
      dedicated_document_id: currentGoogleFields.documentId?.trim() || null,
    };
    // ... (fetch call as before)
    try {
      const response = await fetch('/api/generate-google-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      return {
        queryStringDisplay: result.query_string_display || '',
        url: result.url || '#',
      };
    } catch (error) {
        console.error("Failed to fetch Google query details:", error);
        const errorMessage = error instanceof Error ? error.message : "Error generating query from server.";
        return { queryStringDisplay: errorMessage, url: "#" };
    }
  };

  const assembleQuery = React.useCallback(async (formatToUse: PatentFormat = activeFormat) => { /* ... same ... */ 
    if (formatToUse === 'google') {
      const { queryStringDisplay, url } = await fetchGoogleQueryDetailsFromServer(searchConditions, googleLikeFields);
      onMainInputChange(queryStringDisplay);
      setQueryLinkHref(queryStringDisplay.trim() && !queryStringDisplay.startsWith("Error") && url !=='#' ? url : '#');
    } else if (formatToUse === 'uspto') {
      let queryParts: string[] = [];
      searchConditions.forEach(condition => {
        if (condition.type === 'TEXT') {
          const textData = condition.data as InternalTextSearchData;
          if (!textData.text.trim()) return;
          const terms = textData.text.trim().split(/\s+/).filter(Boolean);
          if (terms.length === 0) return;
          let processedTerms: string;
          switch (textData.termOperator) {
            case 'EXACT': processedTerms = `"${terms.join(' ')}"`; break;
            case 'ANY': processedTerms = terms.length > 1 ? `(${terms.map(t=> t.includes(" ") ? `"${t}"`: t).join(' OR ')})` : (terms[0].includes(" ") ? `"${terms[0]}"`: terms[0]); break;
            case 'NONE': processedTerms = terms.length > 1 ? `NOT (${terms.map(t => t.includes(" ") ? `"${t}"`: t).join(' OR ')})` : `NOT ${terms[0].includes(" ") ? `"${terms[0]}"`: terms[0]}`; break;
            default: processedTerms = terms.length > 1 ? `(${terms.map(t => t.includes(" ") ? `"${t}"`: t).join(' AND ')})` : (terms[0].includes(" ") ? `"${terms[0]}"`: terms[0]); break;
          }
          let fieldSpecificQueryParts: string[] = [];
          if (textData.selectedScopes.has('FT') || textData.selectedScopes.size === 0) {
            fieldSpecificQueryParts.push(processedTerms);
          } else {
            textData.selectedScopes.forEach(scope => {
              if (scope === 'TI') fieldSpecificQueryParts.push(`TTL/(${processedTerms})`);
              else if (scope === 'AB') fieldSpecificQueryParts.push(`ABST/(${processedTerms})`);
              else if (scope === 'CL') fieldSpecificQueryParts.push(`ACLM/(${processedTerms})`);
              else if (scope === 'CPC') fieldSpecificQueryParts.push(`CPC/${processedTerms.replace(/[()]/g, '')}`);
            });
          }
          if (fieldSpecificQueryParts.length > 0) queryParts.push(fieldSpecificQueryParts.length > 1 ? `(${fieldSpecificQueryParts.join(' OR ')})` : fieldSpecificQueryParts[0]);
        } else if (condition.type === 'CLASSIFICATION') {
          const { cpc } = condition.data as ClassificationSearchData;
          if (cpc && cpc.trim()) queryParts.push(`CPC/${cpc.trim()}`);
        }
      });
      const mapDateTypeToUSPTO = (dt: DateType) => { if(dt === 'filing') return 'APD'; if(dt === 'priority') return 'PRD'; return 'ISD'; }
      const usptoDateType = mapDateTypeToUSPTO(googleLikeFields.dateType);
      const formatDateForUSPTO = (dateStr: string) => { if (!dateStr) return ''; const [year, month, day] = dateStr.split('-'); return `${parseInt(month, 10)}/${parseInt(day, 10)}/${year}`; }
      if (googleLikeFields.dateFrom) queryParts.push(`${usptoDateType}/>${formatDateForUSPTO(googleLikeFields.dateFrom)}`);
      if (googleLikeFields.dateTo) queryParts.push(`${usptoDateType}/<${formatDateForUSPTO(googleLikeFields.dateTo)}`);
      if (googleLikeFields.inventors.length > 0) { const invQuery = googleLikeFields.inventors.map(inv => `"${inv.value.trim()}"`).join(' OR '); queryParts.push(`IN/(${invQuery})`); }
      if (googleLikeFields.assignees.length > 0) { const asgQuery = googleLikeFields.assignees.map(asg => `"${asg.value.trim()}"`).join(' OR '); queryParts.push(`AN/(${asgQuery})`); }
      if (googleLikeFields.cpc?.trim()) queryParts.push(`CPC/${googleLikeFields.cpc.trim()}`);
      if (googleLikeFields.specificTitle?.trim()) queryParts.push(`TTL/("${googleLikeFields.specificTitle.trim()}")`);
      if (googleLikeFields.documentId?.trim()) queryParts.push(`PN/("${googleLikeFields.documentId.trim()}")`);
      const assembled = queryParts.filter(Boolean).join(' AND ').trim();
      onMainInputChange(assembled);
      if (assembled.trim()) {
        setQueryLinkHref(`https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsbasic.html?query=${encodeURIComponent(assembled)}`);
      } else {
        setQueryLinkHref('#');
      }
    } else {
      onMainInputChange('');
      setQueryLinkHref('#');
    }
  }, [activeFormat, searchConditions, googleLikeFields, onMainInputChange]);

  useEffect(() => { /* ... same ... */ 
    assembleQuery(activeFormat);
  }, [activeFormat, searchConditions, googleLikeFields, assembleQuery]);

  const renderSearchConditionRow = (condition: SearchCondition, isForNewEntryPlaceholder: boolean, canBeRemoved: boolean): React.ReactNode => { /* ... same ... */ 
    if (condition.type === 'TEXT') {
      const textData = condition.data as InternalTextSearchData;
      return (
        <div className="flex items-center w-full">
          <input type="text" value={textData.text} onChange={(e) => updateSearchConditionText(condition.id, e.target.value)} placeholder={isForNewEntryPlaceholder ? "Type here to add search term..." : "Enter search terms..."} className="flex-grow p-2 border-none focus:ring-0 text-sm bg-transparent outline-none"/>
          {canBeRemoved && (<button onClick={() => removeSearchCondition(condition.id)} className="p-1 text-gray-400 hover:text-red-500 focus:outline-none mr-1 flex-shrink-0" title="Remove search condition"><XCircle size={16} /></button>)}
        </div>
      );
    }
    if (condition.type === 'CLASSIFICATION') {
        const cpcData = condition.data as ClassificationSearchData;
        let displayText = `CPC: ${cpcData.cpc}`;
        if (activeFormat === 'google') { displayText = `cpc:${cpcData.cpc.trim().replace(/\//g, '')}`; } 
        else { displayText = `CPC/${cpcData.cpc.trim()}`; }
        displayText += ` (${cpcData.option === 'CHILDREN' ? 'incl. children' : 'exact'})`;
        return (
            <div className="flex items-center justify-between w-full">
                <span className="text-sm p-2 flex-grow truncate">{displayText}</span>
                {canBeRemoved && (<button onClick={() => removeSearchCondition(condition.id)} className="p-1 text-gray-400 hover:text-red-500 focus:outline-none mr-1 flex-shrink-0" title="Remove search condition"><XCircle size={16} /></button>)}
            </div>
        );
    }
    return (
        <div className="flex items-center justify-between w-full">
            <span className="text-sm p-2 flex-grow text-gray-400 truncate">{`${condition.type.charAt(0).toUpperCase() + condition.type.slice(1).toLowerCase()}: Click tool icon to configure`}</span>
            {canBeRemoved && (<button onClick={() => removeSearchCondition(condition.id)} className="p-1 text-gray-400 hover:text-red-500 focus:outline-none mr-1 flex-shrink-0" title="Remove search condition"><XCircle size={16} /></button>)}
        </div>
    );
  };

  // Generic MultiSelectDropdown Component (can be moved to its own file later)
  interface MultiSelectOption<T extends string> { value: T; label: string; }
  interface MultiSelectDropdownProps<T extends string> {
    label: string;
    icon: React.ReactNode;
    options: Array<MultiSelectOption<T>>;
    selectedValues: T[];
    onToggle: (value: T) => void;
    isOpen: boolean;
    setIsOpen: (isOpen: boolean) => void;
    dropdownRef: React.RefObject<HTMLDivElement>;
  }

  function MultiSelectDropdown<T extends string>({
    label, icon, options, selectedValues, onToggle, isOpen, setIsOpen, dropdownRef
  }: MultiSelectDropdownProps<T>) {
    const displaySelected = () => {
      if (selectedValues.length === 0) return `Any ${label}`;
      if (selectedValues.length <= 2) return selectedValues.map(val => options.find(opt => opt.value === val)?.label || val).join(', ');
      return `${options.find(opt => opt.value === selectedValues[0])?.label}, ${options.find(opt => opt.value === selectedValues[1])?.label}, +${selectedValues.length - 2}`;
    };

    return (
      <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm relative" ref={dropdownRef}>
        <div
          className="flex items-center justify-between cursor-pointer group text-sm"
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className="flex items-center">
            {icon}
            <span className="text-gray-700">{label}</span>
          </div>
          <div className="flex items-center">
            <span className="text-gray-900 font-medium mr-1 truncate max-w-[100px] md:max-w-[150px]">
              {displaySelected()}
            </span>
            <ChevronDown className={`h-4 w-4 text-gray-400 group-hover:text-gray-600 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </div>
        </div>

        {isOpen && (
          <div className="absolute top-full left-0 mt-1 w-full max-h-60 overflow-y-auto bg-white border border-gray-300 rounded-md shadow-lg z-10 py-1">
            {options.map(opt => (
              <div
                key={opt.value}
                onClick={() => onToggle(opt.value)}
                className="flex items-center justify-between px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
              >
                <span>{opt.label}</span>
                {selectedValues.includes(opt.value) && <Check className="h-4 w-4 text-blue-600" />}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center"><h2 className="text-2xl font-semibold text-gray-800">Patent Query Tool</h2></div>
      <div className="flex border-b border-gray-200">
        {formatTabs.map(tab => <button key={tab.value} onClick={() => handleTabClick(tab.value)} className={`flex items-center justify-center px-4 py-3 -mb-px text-sm font-medium focus:outline-none transition-colors duration-150 ${activeFormat === tab.value ? 'border-b-2 border-blue-600 text-blue-600' : 'border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>{tab.icon}{tab.label}</button>)}
      </div>
      <div className="space-y-1 pt-4">
        <a 
          href={mainQueryValue.trim() && !mainQueryValue.startsWith("Error") && queryLinkHref !== '#' ? queryLinkHref : '#'} 
          target="_blank" 
          rel="noopener noreferrer" 
          className={`block text-sm font-medium mb-1 text-center ${mainQueryValue.trim() && !mainQueryValue.startsWith("Error") && queryLinkHref !=='#' ? 'text-blue-600 hover:text-blue-800 hover:underline cursor-pointer' : 'text-gray-700 cursor-default'}`} 
          onClick={(e) => { if (!mainQueryValue.trim() || mainQueryValue.startsWith("Error") || queryLinkHref === '#') e.preventDefault(); }}
        >
          Search Query {mainQueryValue.trim() && !mainQueryValue.startsWith("Error") && queryLinkHref !=='#' && <LinkIcon className="inline-block h-3 w-3 ml-1 mb-0.5" />}
        </a>
        <input id="mainQueryInput" type="text" value={mainQueryValue} onChange={handleMainQueryDirectInputChange} placeholder={`Assembled query...`} className={`block w-full rounded-lg border bg-slate-50 px-4 py-3 text-slate-800 placeholder-slate-400 text-base shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-shadow duration-150 ease-in-out ${mainQueryValue.startsWith("Error") ? 'border-red-500 text-red-700' : ''}`}/>
      </div>
      <div className="pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-medium text-gray-700 flex items-center"><Wand2 className="h-5 w-5 mr-2 text-blue-600" />Search Terms</h3>
        </div>
        <div className="p-4 border border-gray-200 rounded-lg space-y-3 bg-gray-50 shadow">
          {searchConditions.map((condition, index) => {
            const isLastCondition = index === searchConditions.length - 1;
            const isTextCondition = condition.type === 'TEXT';
            const textData = isTextCondition ? (condition.data as InternalTextSearchData) : { text: '' };
            const isForNewEntryPlaceholder = isLastCondition && isTextCondition && textData.text.trim() === '';
            const canBeRemoved = !(searchConditions.length === 1 && isTextCondition && textData.text.trim() === '');
            return (
                <div key={condition.id} className="border border-gray-300 rounded-md bg-white shadow-sm flex items-stretch">
                <div className="flex-grow min-w-0 border-r border-gray-300">
                    {renderSearchConditionRow(condition, isForNewEntryPlaceholder, canBeRemoved)}
                </div>
                <button onClick={() => handleOpenSearchToolModal(condition)} className="p-2 text-gray-600 hover:bg-gray-100 rounded-r-md flex items-center justify-center focus:outline-none focus:ring-1 focus:ring-blue-500 flex-shrink-0" title={`Change tool type (current: ${condition.type})`} style={{ minWidth: '40px' }}>
                    {getConditionTypeIcon(condition.type)}
                </button>
                </div>
            );
          })}
        </div>
      </div>
      <div className="pt-4 border-t border-gray-200">
        <h3 className="text-lg font-medium text-gray-700 mb-3">Search Fields</h3>
        <div className="p-4 border border-gray-200 rounded-lg space-y-3 bg-gray-50 shadow">
            <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm space-y-2">
                <div className="flex items-center justify-between">
                    <div className="flex items-center"><CalendarDays className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" /><span className="text-sm font-medium text-gray-700">Date</span></div>
                    <div className="relative group flex-shrink-0" style={{minWidth: '150px'}}>
                        <div className="inline-flex items-center justify-end cursor-pointer p-1.5 rounded-md hover:bg-gray-100 w-full border border-gray-300 shadow-sm bg-white"><span className="text-sm text-gray-700 mr-1 truncate">{getDateTypeLabel(googleLikeFields.dateType)}</span><ChevronDown className="h-4 w-4 text-gray-400 group-hover:text-gray-600 ml-auto" /></div>
                        <select value={googleLikeFields.dateType} onChange={e => handleGoogleLikeFieldChange('dateType', e.target.value as DateType)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer appearance-none" aria-label="Select date type">{dateTypeOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}</select>
                    </div>
                </div>
                <div className="flex items-center space-x-2">
                    <input type="date" value={googleLikeFields.dateFrom} onChange={e => handleGoogleLikeFieldChange('dateFrom', e.target.value)} className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-1.5 text-xs" placeholder="From"/>
                    <span className="text-gray-500 text-sm">–</span>
                    <input type="date" value={googleLikeFields.dateTo} onChange={e => handleGoogleLikeFieldChange('dateTo', e.target.value)} className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-1.5 text-xs" placeholder="To"/>
                </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm">
                    <label className="flex items-center text-sm font-medium text-gray-700 mb-1"><Users className="h-5 w-5 text-gray-500 mr-2" />Inventor(s)</label>
                    <div className="flex flex-wrap gap-x-1.5 gap-y-1 items-center mb-1.5 min-h-[24px]">
                        {googleLikeFields.inventors.map((inv, index) => (<React.Fragment key={inv.id}>{index > 0 && <span className="text-xs text-gray-400">or</span>}<span className="inline-flex items-center py-0.5 pl-2 pr-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 whitespace-nowrap">{inv.value}<button onClick={() => removeDynamicFieldEntry('inventors', inv.id)} className="ml-1 flex-shrink-0 text-blue-400 hover:text-blue-600 focus:outline-none"><XCircle className="h-3.5 w-3.5" /></button></span></React.Fragment>))}
                    </div>
                    <input ref={inventorInputRef} type="text" value={currentInventorInput} onChange={e => setCurrentInventorInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addDynamicFieldEntry('inventors');}}} onBlur={() => {if(currentInventorInput.trim()) addDynamicFieldEntry('inventors');}} placeholder="+ Inventor" className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-1.5 text-xs"/>
                </div>
                <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm">
                    <label className="flex items-center text-sm font-medium text-gray-700 mb-1"><Briefcase className="h-5 w-5 text-gray-500 mr-2" />Assignee(s)</label>
                    <div className="flex flex-wrap gap-x-1.5 gap-y-1 items-center mb-1.5 min-h-[24px]">
                        {googleLikeFields.assignees.map((asg, index) => (<React.Fragment key={asg.id}>{index > 0 && <span className="text-xs text-gray-400">or</span>}<span className="inline-flex items-center py-0.5 pl-2 pr-1 rounded-full text-xs font-medium bg-green-100 text-green-700 whitespace-nowrap">{asg.value}<button onClick={() => removeDynamicFieldEntry('assignees', asg.id)} className="ml-1 flex-shrink-0 text-green-400 hover:text-green-600 focus:outline-none"><XCircle className="h-3.5 w-3.5" /></button></span></React.Fragment>))}
                    </div>
                    <input ref={assigneeInputRef} type="text" value={currentAssigneeInput} onChange={e => setCurrentAssigneeInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addDynamicFieldEntry('assignees');}}} onBlur={() => {if(currentAssigneeInput.trim()) addDynamicFieldEntry('assignees');}} placeholder="+ Assignee" className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-1.5 text-xs"/>
                </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <MultiSelectDropdown
                    label="Patent Office(s)"
                    icon={<Globe className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" />}
                    options={patentOfficeOptions}
                    selectedValues={googleLikeFields.patentOffices}
                    onToggle={handlePatentOfficeToggle}
                    isOpen={isPatentOfficeDropdownOpen}
                    setIsOpen={setIsPatentOfficeDropdownOpen}
                    dropdownRef={patentOfficeRef}
                />
                <MultiSelectDropdown
                    label="Language(s)"
                    icon={<Languages className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" />}
                    options={languageOptions}
                    selectedValues={googleLikeFields.languages}
                    onToggle={handleLanguageToggle}
                    isOpen={isLanguageDropdownOpen}
                    setIsOpen={setIsLanguageDropdownOpen}
                    dropdownRef={languageRef}
                />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm flex items-center justify-between cursor-pointer group relative text-sm" onClick={() => (document.getElementById(`statusSelect`) as HTMLSelectElement)?.focus()}>
                    <div className="flex items-center"><Filter size={18} className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" /><span className="text-gray-700">Status</span></div>
                    <div className="flex items-center"><span className="text-gray-900 font-medium mr-1 truncate max-w-[100px] md:max-w-[150px]">{patentStatusOptions.find(opt => opt.value === googleLikeFields.status)?.label || `Any`}</span><ChevronDown className="h-4 w-4 text-gray-400 group-hover:text-gray-600" /></div>
                    <select id={`statusSelect`} value={googleLikeFields.status} onChange={e => handleGoogleLikeFieldChange('status', e.target.value as PatentStatus)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer appearance-none">{patentStatusOptions.map(opt => <option key={opt.value || `any-status`} value={opt.value}>{opt.label}</option>)}</select>
                </div>
                <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm flex items-center justify-between cursor-pointer group relative text-sm" onClick={() => (document.getElementById(`patentTypeSelect`) as HTMLSelectElement)?.focus()}>
                    <div className="flex items-center"><TypeIcon size={18} className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" /><span className="text-gray-700">Type</span></div>
                    <div className="flex items-center"><span className="text-gray-900 font-medium mr-1 truncate max-w-[100px] md:max-w-[150px]">{patentTypeOptions.find(opt => opt.value === googleLikeFields.patentType)?.label || `Any`}</span><ChevronDown className="h-4 w-4 text-gray-400 group-hover:text-gray-600" /></div>
                    <select id={`patentTypeSelect`} value={googleLikeFields.patentType} onChange={e => handleGoogleLikeFieldChange('patentType', e.target.value as PatentType)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer appearance-none">{patentTypeOptions.map(opt => <option key={opt.value || `any-type`} value={opt.value}>{opt.label}</option>)}</select>
                </div>
            </div>
            <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm flex items-center justify-between cursor-pointer group relative text-sm" onClick={() => (document.getElementById(`litigationStatusSelect`) as HTMLSelectElement)?.focus()}>
                <div className="flex items-center"><ShieldQuestion className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" /><span className="text-gray-700">Litigation Status</span></div>
                <div className="flex items-center">
                    <span className="text-gray-900 font-medium mr-1 truncate max-w-[100px] md:max-w-[150px]">
                        {getLitigationStatusLabel(googleLikeFields.litigation)}
                    </span>
                    <ChevronDown className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
                </div>
                <select id={`litigationStatusSelect`} value={googleLikeFields.litigation} onChange={e => handleGoogleLikeFieldChange('litigation', e.target.value as LitigationStatus)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer appearance-none" aria-label="Select litigation status">
                    {litigationStatusOptions.map(opt => <option key={opt.value || 'any-litigation'} value={opt.value}>{opt.label}</option>)}
                </select>
            </div>
        </div>
      </div>

      {isSearchToolModalOpen && editingCondition && (
        <SearchToolModal
            isOpen={isSearchToolModalOpen}
            onClose={handleCloseSearchToolModal}
            onUpdateCondition={handleUpdateSearchConditionFromModal}
            initialCondition={editingCondition}
        />
      )}
    </div>
  );
};
export default ChatInput;
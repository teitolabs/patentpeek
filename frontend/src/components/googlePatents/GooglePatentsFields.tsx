// src/components/googlePatents/GooglePatentsFields.tsx
import React from 'react';
import {
    CalendarDays, ChevronDown, Users, Briefcase, XCircle,
    Globe, Check, Languages, Filter, Type as TypeIcon, ShieldQuestion
} from 'lucide-react';
import {
    DateType, PatentOffice, Language, PatentStatus, PatentType, LitigationStatus
} from '../searchToolTypes';

export interface GoogleLikeSearchFields {
  dateFrom: string; dateTo: string; dateType: DateType;
  inventors: Array<{ id: string; value: string }>;
  assignees: Array<{ id: string; value: string }>;
  patentOffices: PatentOffice[];
  languages: Language[];
  status: PatentStatus; patentType: PatentType;
  litigation: LitigationStatus;
}

export const dateTypeOptions: Array<{value: DateType; label: string}> = [
    {value: 'publication', label: 'Publication'}, {value: 'priority', label: 'Priority'}, {value: 'filing', label: 'Filing'},
];

export const patentOfficeOptions: Array<{value: PatentOffice; label: string}> = [
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
    {value: 'BY', label: 'BY'}, {value: 'BZ', label: 'BZ'}, {value: 'CA', label: 'CA'},
    {value: 'CF', label: 'CF'}, {value: 'CG', label: 'CG'}, {value: 'CH', label: 'CH'},
    {value: 'CI', label: 'CI'}, {value: 'CL', label: 'CL'}, {value: 'CM', label: 'CM'},
    {value: 'CO', label: 'CO'}, {value: 'CR', label: 'CR'}, {value: 'CS', label: 'CS'},
    {value: 'CU', label: 'CU'}, {value: 'CY', label: 'CY'}, {value: 'CZ', label: 'CZ'},
    {value: 'DD', label: 'DD'}, {value: 'DE', label: 'DE'},
    {value: 'DJ', label: 'DJ'}, {value: 'DK', label: 'DK'}, {value: 'DM', label: 'DM'},
    {value: 'DO', label: 'DO'}, {value: 'DZ', label: 'DZ'}, {value: 'EA', label: 'EA'},
    {value: 'EC', label: 'EC'}, {value: 'EE', label: 'EE'}, {value: 'EG', label: 'EG'},
    {value: 'EM', label: 'EM'}, {value: 'ES', label: 'ES'}, {value: 'FI', label: 'FI'},
    {value: 'FR', label: 'FR'},
    {value: 'GA', label: 'GA'}, {value: 'GB', label: 'GB'},
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
];

export const languageOptions: Array<{value: Language; label: string}> = [
    {value: 'ENGLISH', label: 'English'}, {value: 'GERMAN', label: 'German'},
    {value: 'CHINESE', label: 'Chinese'}, {value: 'FRENCH', label: 'French'},
    {value: 'SPANISH', label: 'Spanish'}, {value: 'ARABIC', label: 'Arabic'},
    {value: 'JAPANESE', label: 'Japanese'}, {value: 'KOREAN', label: 'Korean'},
    {value: 'PORTUGUESE', label: 'Portuguese'}, {value: 'RUSSIAN', label: 'Russian'},
    {value: 'ITALIAN', label: 'Italian'}, {value: 'DUTCH', label: 'Dutch'},
    {value: 'SWEDISH', label: 'Swedish'}, {value: 'FINNISH', label: 'Finnish'},
    {value: 'NORWEGIAN', label: 'Norwegian'}, {value: 'DANISH', label: 'Danish'}
];

export const patentStatusOptions: Array<{value: PatentStatus; label: string}> = [ {value: '', label: 'Any Status'}, {value: 'GRANT', label: 'Grant'}, {value: 'APPLICATION', label: 'Application'}, ];
export const patentTypeOptions: Array<{value: PatentType; label: string}> = [
    {value: '', label: 'Any Type'},
    {value: 'PATENT', label: 'Patent'}, // Simplified label
    {value: 'DESIGN', label: 'Design'},
];
export const litigationStatusOptions: Array<{value: LitigationStatus; label: string}> = [
    {value: '', label: 'Any Litigation'}, {value: 'YES', label: 'Has Related Litigation'}, {value: 'NO', label: 'No Known Litigation'},
];

export function getDateTypeLabel(value: DateType): string { return dateTypeOptions.find(opt => opt.value === value)?.label || 'Select Type';}
export function getLitigationStatusLabel(value: LitigationStatus): string { return litigationStatusOptions.find(opt => opt.value === value)?.label || 'Any Litigation';}

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

interface GooglePatentsFieldsProps {
  fields: GoogleLikeSearchFields;
  onFieldChange: <K extends keyof GoogleLikeSearchFields>(field: K, value: GoogleLikeSearchFields[K]) => void;
  onPatentOfficeToggle: (officeCode: PatentOffice) => void;
  onLanguageToggle: (langCode: Language) => void;
  onAddDynamicEntry: (field: 'inventors' | 'assignees') => void;
  onRemoveDynamicEntry: (field: 'inventors' | 'assignees', id: string) => void;
  currentInventorInput: string;
  setCurrentInventorInput: (val: string) => void;
  currentAssigneeInput: string;
  setCurrentAssigneeInput: (val: string) => void;
  inventorInputRef: React.RefObject<HTMLInputElement>;
  assigneeInputRef: React.RefObject<HTMLInputElement>;
  isPatentOfficeDropdownOpen: boolean;
  setIsPatentOfficeDropdownOpen: (isOpen: boolean) => void;
  isLanguageDropdownOpen: boolean;
  setIsLanguageDropdownOpen: (isOpen: boolean) => void;
  patentOfficeRef: React.RefObject<HTMLDivElement>;
  languageRef: React.RefObject<HTMLDivElement>;
}

const GooglePatentsFields: React.FC<GooglePatentsFieldsProps> = ({
  fields, onFieldChange, onPatentOfficeToggle, onLanguageToggle,
  onAddDynamicEntry, onRemoveDynamicEntry,
  currentInventorInput, setCurrentInventorInput,
  currentAssigneeInput, setCurrentAssigneeInput,
  inventorInputRef, assigneeInputRef,
  isPatentOfficeDropdownOpen, setIsPatentOfficeDropdownOpen,
  isLanguageDropdownOpen, setIsLanguageDropdownOpen,
  patentOfficeRef, languageRef
}) => {
  return (
    <div className="p-4 border border-gray-200 rounded-lg space-y-3 bg-gray-50 shadow">
        <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm space-y-2">
            <div className="flex items-center justify-between">
                <div className="flex items-center"><CalendarDays className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" /><span className="text-sm font-medium text-gray-700">Date</span></div>
                <div className="relative group flex-shrink-0" style={{minWidth: '150px'}}>
                    <div className="inline-flex items-center justify-end cursor-pointer p-1.5 rounded-md hover:bg-gray-100 w-full border border-gray-300 shadow-sm bg-white"><span className="text-sm text-gray-700 mr-1 truncate">{getDateTypeLabel(fields.dateType)}</span><ChevronDown className="h-4 w-4 text-gray-400 group-hover:text-gray-600 ml-auto" /></div>
                    <select value={fields.dateType} onChange={e => onFieldChange('dateType', e.target.value as DateType)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer appearance-none" aria-label="Select date type">{dateTypeOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}</select>
                </div>
            </div>
            <div className="flex items-center space-x-2">
                <input type="date" value={fields.dateFrom} onChange={e => onFieldChange('dateFrom', e.target.value)} className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-1.5 text-xs" placeholder="From"/>
                <span className="text-gray-500 text-sm">–</span>
                <input type="date" value={fields.dateTo} onChange={e => onFieldChange('dateTo', e.target.value)} className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-1.5 text-xs" placeholder="To"/>
            </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm">
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1"><Users className="h-5 w-5 text-gray-500 mr-2" />Inventor(s)</label>
                <div className="flex flex-wrap gap-x-1.5 gap-y-1 items-center mb-1.5 min-h-[24px]">
                    {fields.inventors.map((inv, index) => (<React.Fragment key={inv.id}>{index > 0 && <span className="text-xs text-gray-400">or</span>}<span className="inline-flex items-center py-0.5 pl-2 pr-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 whitespace-nowrap">{inv.value}<button onClick={() => onRemoveDynamicEntry('inventors', inv.id)} className="ml-1 flex-shrink-0 text-blue-400 hover:text-blue-600 focus:outline-none"><XCircle className="h-3.5 w-3.5" /></button></span></React.Fragment>))}
                </div>
                <input ref={inventorInputRef} type="text" value={currentInventorInput} onChange={e => setCurrentInventorInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); onAddDynamicEntry('inventors');}}} onBlur={() => {if(currentInventorInput.trim()) onAddDynamicEntry('inventors');}} placeholder="+ Inventor" className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-1.5 text-xs"/>
            </div>
            <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm">
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1"><Briefcase className="h-5 w-5 text-gray-500 mr-2" />Assignee(s)</label>
                <div className="flex flex-wrap gap-x-1.5 gap-y-1 items-center mb-1.5 min-h-[24px]">
                    {fields.assignees.map((asg, index) => (<React.Fragment key={asg.id}>{index > 0 && <span className="text-xs text-gray-400">or</span>}<span className="inline-flex items-center py-0.5 pl-2 pr-1 rounded-full text-xs font-medium bg-green-100 text-green-700 whitespace-nowrap">{asg.value}<button onClick={() => onRemoveDynamicEntry('assignees', asg.id)} className="ml-1 flex-shrink-0 text-green-400 hover:text-green-600 focus:outline-none"><XCircle className="h-3.5 w-3.5" /></button></span></React.Fragment>))}
                </div>
                <input ref={assigneeInputRef} type="text" value={currentAssigneeInput} onChange={e => setCurrentAssigneeInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); onAddDynamicEntry('assignees');}}} onBlur={() => {if(currentAssigneeInput.trim()) onAddDynamicEntry('assignees');}} placeholder="+ Assignee" className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-1.5 text-xs"/>
            </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <MultiSelectDropdown
                label="Patent Office(s)"
                icon={<Globe className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" />}
                options={patentOfficeOptions}
                selectedValues={fields.patentOffices}
                onToggle={onPatentOfficeToggle}
                isOpen={isPatentOfficeDropdownOpen}
                setIsOpen={setIsPatentOfficeDropdownOpen}
                dropdownRef={patentOfficeRef}
            />
            <MultiSelectDropdown
                label="Language(s)"
                icon={<Languages className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" />}
                options={languageOptions}
                selectedValues={fields.languages}
                onToggle={onLanguageToggle}
                isOpen={isLanguageDropdownOpen}
                setIsOpen={setIsLanguageDropdownOpen}
                dropdownRef={languageRef}
            />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm flex items-center justify-between cursor-pointer group relative text-sm" onClick={() => (document.getElementById(`statusSelect`) as HTMLSelectElement)?.focus()}>
                <div className="flex items-center"><Filter size={18} className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" /><span className="text-gray-700">Status</span></div>
                <div className="flex items-center"><span className="text-gray-900 font-medium mr-1 truncate max-w-[100px] md:max-w-[150px]">{patentStatusOptions.find(opt => opt.value === fields.status)?.label || `Any`}</span><ChevronDown className="h-4 w-4 text-gray-400 group-hover:text-gray-600" /></div>
                <select id={`statusSelect`} value={fields.status} onChange={e => onFieldChange('status', e.target.value as PatentStatus)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer appearance-none">{patentStatusOptions.map(opt => <option key={opt.value || `any-status`} value={opt.value}>{opt.label}</option>)}</select>
            </div>
            <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm flex items-center justify-between cursor-pointer group relative text-sm" onClick={() => (document.getElementById(`patentTypeSelect`) as HTMLSelectElement)?.focus()}>
                <div className="flex items-center"><TypeIcon size={18} className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" /><span className="text-gray-700">Type</span></div>
                <div className="flex items-center"><span className="text-gray-900 font-medium mr-1 truncate max-w-[100px] md:max-w-[150px]">{patentTypeOptions.find(opt => opt.value === fields.patentType)?.label || `Any`}</span><ChevronDown className="h-4 w-4 text-gray-400 group-hover:text-gray-600" /></div>
                <select id={`patentTypeSelect`} value={fields.patentType} onChange={e => onFieldChange('patentType', e.target.value as PatentType)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer appearance-none">{patentTypeOptions.map(opt => <option key={opt.value || `any-type`} value={opt.value}>{opt.label}</option>)}</select>
            </div>
        </div>
        <div className="p-3 border-gray-300 rounded-md bg-white shadow-sm flex items-center justify-between cursor-pointer group relative text-sm" onClick={() => (document.getElementById(`litigationStatusSelect`) as HTMLSelectElement)?.focus()}>
            <div className="flex items-center"><ShieldQuestion className="h-5 w-5 text-gray-500 mr-2 flex-shrink-0" /><span className="text-gray-700">Litigation Status</span></div>
            <div className="flex items-center">
                <span className="text-gray-900 font-medium mr-1 truncate max-w-[100px] md:max-w-[150px]">
                    {getLitigationStatusLabel(fields.litigation)}
                </span>
                <ChevronDown className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
            </div>
            <select id={`litigationStatusSelect`} value={fields.litigation} onChange={e => onFieldChange('litigation', e.target.value as LitigationStatus)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer appearance-none" aria-label="Select litigation status">
                {litigationStatusOptions.map(opt => <option key={opt.value || 'any-litigation'} value={opt.value}>{opt.label}</option>)}
            </select>
        </div>
    </div>
  );
};

export default GooglePatentsFields;
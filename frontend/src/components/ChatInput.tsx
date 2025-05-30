// --- START OF FILE ChatInput.tsx ---
import React, { useState, useEffect, useRef } from 'react';
import { PatentFormat } from '../types';
import {
    Building2, XCircle, Filter, Settings2, Type as TypeIcon, Wand2, Link as LinkIcon,
    FlaskConical, Ruler, Hash,
} from 'lucide-react';
import SearchToolModal, { ModalToolData } from './SearchToolModal';
import {
    SearchCondition, SearchToolType, TextSearchCondition, InternalTextSearchData,
    PatentOffice, Language, DateType // Added DateType
} from './searchToolTypes';

import GooglePatentsFields, { GoogleLikeSearchFields } from './googlePatents/GooglePatentsFields';
import { generateGoogleQuery } from './googlePatents/googleQueryBuilder';
import UsptoPatentsFields from './usptoPatents/UsptoPatentsFields';
// Remove USPTO local query builder if fully replaced, or keep for helpers
// import { generateUsptoQuery, UsptoSpecificSettings } from './usptoPatents/usptoQueryBuilder';


export interface ChatInputProps {
  value: string;
  activeFormat: PatentFormat;
  onTabChange: (newFormat: PatentFormat) => void;
  onMainInputChange: (text: string) => void;
}

function GoogleGIcon(): React.ReactElement { return (<svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M12.2446 10.925L12.2446 14.005L18.7746 14.005C18.5346 15.095 18.0546 16.125 17.3446 16.965C16.5846 17.855 15.2746 18.665 13.4846 18.665C10.6846 18.665 8.31462 16.375 8.31462 13.495C8.31462 10.615 10.6846 8.32502 13.4846 8.32502C14.9346 8.32502 16.0046 8.92502 16.9546 9.81502L19.1146 7.71502C17.6746 6.38502 15.8046 5.32502 13.4846 5.32502C9.86462 5.32502 6.91462 8.22502 6.91462 11.995C6.91462 15.765 9.86462 18.665 13.4846 18.665C15.9146 18.665 17.7246 17.835 19.0646 16.415C20.4746 14.925 20.9846 12.925 20.9846 11.495C20.9846 10.925 20.9446 10.475 20.8546 10.005L13.4846 10.005L12.2446 10.925Z" /></svg>);}

function getConditionTypeIcon(type: SearchToolType): React.ReactElement {
    switch(type) {
        case 'TEXT': return <TypeIcon size={18} className="text-gray-600" />;
        case 'CLASSIFICATION': return <Filter size={18} className="text-gray-600" />;
        case 'CHEMISTRY': return <FlaskConical size={18} className="text-orange-600" />;
        case 'MEASURE': return <Ruler size={18} className="text-purple-600" />;
        case 'NUMBERS': return <Hash size={18} className="text-teal-600" />;
        default:
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const _exhaustiveCheck: never = type;
            console.error("Unhandled SearchToolType in getConditionTypeIcon:", type);
            return <Settings2 size={18} className="text-gray-600" />;
    }
}

const formatTabs: Array<{ value: PatentFormat; label: string; icon: React.ReactNode }> = [
  { value: 'google', label: 'Google Patents', icon: <GoogleGIcon /> },
  { value: 'uspto', label: 'USPTO', icon: <Building2 className="h-5 w-5 mr-2" /> },
];

// Helper function to map Google-like dateType to USPTO field codes
const mapDateTypeToUSPTO_local = (dt: DateType): string => {
    if(dt === 'filing') return 'AD'; // Application Date (USPTO uses AD for app filing date)
    // if(dt === 'priority') return 'PRD'; // Priority Date (USPTO uses APD for app priority date, less common for general search)
    // For simplicity, let's map priority to APD (Application Priority Date) if needed, or just use PD/ISD for most common cases.
    // The backend uspto_generate_query.py uses PD (Publication Date), AD (Application Filing Date), ISD (Issue Date), AY (App Year), PY (Pub Year)
    // Let's stick to common ones or ensure backend handles PRD if we send it.
    // For now, 'priority' from Google often means 'earliest priority date'.
    // USPTO's 'APD' for "Application filing date" seems the closest general one if not specific.
    // Given the backend's DATE type uses `field` like 'PD', 'AD', 'ISD', 'AY', 'PY', 'PRD'
    // we can map 'priority' to 'PRD'.
    if(dt === 'priority') return 'PRD';
    return 'PD'; // Publication Date (default, or ISD for Issue Date, PD is more general)
  }
  
// Helper function to format YYYY-MM-DD to MM/DD/YYYY for USPTO date expressions
const formatDateForUSPTO_local = (dateStr: string): string => {
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-');
    if (!year || !month || !day || year.length !== 4 || month.length !== 2 || day.length !== 2) {
        console.warn(`Invalid date string for USPTO formatting: ${dateStr}`);
        return ''; // Return empty or throw error if strict validation needed
    }
    return `${parseInt(month, 10)}/${parseInt(day, 10)}/${year}`;
}


const ChatInput: React.FC<ChatInputProps> = ({
  value: mainQueryValue, activeFormat, onTabChange, onMainInputChange,
}) => {
  const createDefaultTextCondition = (): TextSearchCondition => ({
    id: crypto.randomUUID(),
    type: 'TEXT',
    data: { text: '', selectedScopes: new Set(['FT']), termOperator: 'ALL' }
  });

  const [searchConditions, setSearchConditions] = useState<SearchCondition[]>([createDefaultTextCondition()]);
  const [googleLikeFields, setGoogleLikeFields] = useState<GoogleLikeSearchFields>({
    dateFrom: '', dateTo: '', dateType: 'publication',
    inventors: [], assignees: [],
    patentOffices: [],
    languages: [],
    status: '', patentType: '',
    litigation: '',
    cpc: '', specificTitle: '', documentId: ''
  });
  const [currentInventorInput, setCurrentInventorInput] = useState('');
  const [currentAssigneeInput, setCurrentAssigneeInput] = useState('');
  const inventorInputRef = useRef<HTMLInputElement>(null);
  const assigneeInputRef = useRef<HTMLInputElement>(null);
  const [isSearchToolModalOpen, setIsSearchToolModalOpen] = useState(false);
  const [editingCondition, setEditingCondition] = useState<SearchCondition | undefined>(undefined);
  const [queryLinkHref, setQueryLinkHref] = useState<string>('#');

  const [isPatentOfficeDropdownOpen, setIsPatentOfficeDropdownOpen] = useState(false);
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
  const patentOfficeRef = useRef<HTMLDivElement>(null);
  const languageRef = useRef<HTMLDivElement>(null);

  // USPTO Specific State
  const [usptoDefaultOperator, setUsptoDefaultOperator] = useState<string>('OR');
  const [usptoHighlights, setUsptoHighlights] = useState<string>('SINGLE_COLOR');
  const [usptoShowErrors, setUsptoShowErrors] = useState<boolean>(true);
  const [usptoPlurals, setUsptoPlurals] = useState<boolean>(false);
  const [usptoBritishEquivalents, setUsptoBritishEquivalents] = useState<boolean>(true);
  const [usptoSelectedDatabases, setUsptoSelectedDatabases] = useState<string[]>(['US-PGPUB', 'USPAT', 'USOCR']);


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
  const handleTabClick = (newFormat: PatentFormat) => {
    if (newFormat !== activeFormat) {
      if (newFormat === 'uspto') {
        const currentFirstCondition = searchConditions[0];
        if (searchConditions.length > 1 || (currentFirstCondition && currentFirstCondition.type !== 'TEXT')) {
            const newTextCondition = createDefaultTextCondition();
            if (currentFirstCondition && currentFirstCondition.type === 'TEXT' && typeof (currentFirstCondition.data as InternalTextSearchData).text === 'string') {
                newTextCondition.data.text = (currentFirstCondition.data as InternalTextSearchData).text;
            }
            setSearchConditions([newTextCondition]);
        } else if (searchConditions.length === 0) {
            setSearchConditions([createDefaultTextCondition()]);
        }
      }
      onTabChange(newFormat);
    }
  };

  const handleOpenSearchToolModal = (conditionToEdit: SearchCondition) => {
    setEditingCondition(conditionToEdit);
    setIsSearchToolModalOpen(true);
  };
  const handleCloseSearchToolModal = () => {
    setIsSearchToolModalOpen(false);
    setEditingCondition(undefined);
  };
  const handleUpdateSearchConditionFromModal = (conditionId: string, newType: SearchToolType, newData: ModalToolData) => {
    setSearchConditions(prev =>
      prev.map(sc => {
        if (sc.id === conditionId) {
          return { ...sc, type: newType, data: newData as any };
        }
        return sc;
      })
    );
    handleCloseSearchToolModal();
  };

  const removeSearchCondition = (id: string) => {
    setSearchConditions(prev => {
        if (activeFormat === 'uspto' && prev.length === 1 && prev[0].id === id && prev[0].type === 'TEXT') {
            return [{ ...prev[0], data: { ...(prev[0].data as InternalTextSearchData), text: '' } }];
        }
        let newConditions = prev.filter(sc => sc.id !== id);
        if (newConditions.length === 0 && activeFormat !== 'uspto') {
            newConditions = [createDefaultTextCondition()];
        } else if (newConditions.length === 0 && activeFormat === 'uspto') {
            newConditions = [createDefaultTextCondition()];
        }
        if (activeFormat !== 'uspto' && newConditions.length > 0) {
            const lastCondition = newConditions[newConditions.length - 1];
            const lastIsFilledText = lastCondition.type === 'TEXT' && (lastCondition.data as InternalTextSearchData).text.trim() !== '';
            const lastIsNonText = lastCondition.type !== 'TEXT';
            if (lastIsNonText || lastIsFilledText) {
                newConditions.push(createDefaultTextCondition());
            }
        }
        return newConditions;
    });
  };

  const updateSearchConditionText = (id: string, newText: string) => {
    setSearchConditions(prevConditions => {
      let updatedConditions = prevConditions.map(sc =>
        (sc.id === id && sc.type === 'TEXT') ? { ...sc, data: { ...(sc.data as InternalTextSearchData), text: newText } } : sc
      );
      if (activeFormat !== 'uspto') {
        const conditionIndex = updatedConditions.findIndex(sc => sc.id === id);
        if (conditionIndex === -1) return updatedConditions;

        const currentCondition = updatedConditions[conditionIndex];
        if (currentCondition.type === 'TEXT') {
          const textData = currentCondition.data as InternalTextSearchData;
          const isCurrentTextFilled = textData.text.trim() !== '';
          const isCurrentTextEmpty = textData.text.trim() === '';

          if (isCurrentTextFilled && conditionIndex === updatedConditions.length - 1) {
            updatedConditions.push(createDefaultTextCondition());
          }
          else if (isCurrentTextEmpty && updatedConditions.length > 1 && conditionIndex < updatedConditions.length - 1) {
             updatedConditions.splice(conditionIndex, 1);
          }
        }
        if (updatedConditions.length === 0) {
          updatedConditions = [createDefaultTextCondition()];
        }
      }
      return updatedConditions;
    });
  };

  const handleGoogleLikeFieldChange = <K extends keyof GoogleLikeSearchFields>(field: K, value: GoogleLikeSearchFields[K]) => {
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
  const addDynamicFieldEntry = (field: 'inventors' | 'assignees') => {
    const currentInput = field === 'inventors' ? currentInventorInput : currentAssigneeInput;
    const setCurrentInput = field === 'inventors' ? setCurrentInventorInput : setCurrentAssigneeInput;
    const inputRef = field === 'inventors' ? inventorInputRef : assigneeInputRef;
    if (currentInput.trim()) {
      setGoogleLikeFields(prev => ({...prev, [field]: [...prev[field], { id: crypto.randomUUID(), value: currentInput.trim() }]}));
      setCurrentInput(''); inputRef.current?.focus();
    }
  };
  const removeDynamicFieldEntry = (field: 'inventors' | 'assignees', id: string) => {
    setGoogleLikeFields(prev => ({...prev, [field]: prev[field].filter(entry => entry.id !== id)}));
  };


  const assembleQuery = React.useCallback(async (formatToUse: PatentFormat = activeFormat) => {
    let queryResult = { queryStringDisplay: '', url: '#' };
    if (formatToUse === 'google') {
      queryResult = await generateGoogleQuery(searchConditions, googleLikeFields);
    } else if (formatToUse === 'uspto') {
        const backendApiConditions: any[] = [];

        const usptoSearchText = searchConditions.length > 0 && searchConditions[0].type === 'TEXT'
                                ? (searchConditions[0].data as InternalTextSearchData).text
                                : '';

        if (usptoSearchText.trim()) {
            backendApiConditions.push({
            type: 'TEXT',
            data: {
                text: usptoSearchText.trim(),
                field: 'ALL', // User can embed field codes like TTL/ in the text
                multi_word_op: usptoDefaultOperator,
                is_exact: false // Python script handles quotes if user provides them
            }
            });
        }

        if (googleLikeFields.inventors.length > 0) {
            googleLikeFields.inventors.forEach(inv => {
            if (inv.value.trim()) {
                backendApiConditions.push({
                type: 'INVENTOR',
                data: { name: inv.value.trim(), multi_word_op: 'ADJ' }
                });
            }
            });
        }

        if (googleLikeFields.assignees.length > 0) {
            googleLikeFields.assignees.forEach(asg => {
            if (asg.value.trim()) {
                backendApiConditions.push({
                type: 'ASSIGNEE',
                data: { name: asg.value.trim(), multi_word_op: 'ADJ' }
                });
            }
            });
        }
        
        if (googleLikeFields.dateFrom) {
            const formattedDate = formatDateForUSPTO_local(googleLikeFields.dateFrom);
            if (formattedDate) {
                backendApiConditions.push({
                type: 'DATE',
                data: {
                    field: mapDateTypeToUSPTO_local(googleLikeFields.dateType),
                    expression: `>=${formattedDate}`
                }
                });
            }
        }
        if (googleLikeFields.dateTo) {
            const formattedDate = formatDateForUSPTO_local(googleLikeFields.dateTo);
            if (formattedDate) {
                backendApiConditions.push({
                type: 'DATE',
                data: {
                    field: mapDateTypeToUSPTO_local(googleLikeFields.dateType),
                    expression: `<=${formattedDate}`
                }
                });
            }
        }

        if (googleLikeFields.cpc?.trim()) {
            backendApiConditions.push({
            type: 'CLASSIFICATION',
            data: { value: googleLikeFields.cpc.trim(), class_type: 'CPC' }
            });
        }

        if (googleLikeFields.specificTitle?.trim()) {
            backendApiConditions.push({
            type: 'TEXT', // Using TEXT type with TI field for title
            data: {
                text: googleLikeFields.specificTitle.trim(),
                field: 'TI', // Or 'TTL' if backend prefers
                is_exact: true, // Typically titles are searched as exact phrases
                multi_word_op: 'ADJ'
            }
            });
        }

        if (googleLikeFields.documentId?.trim()) {
             // Backend Python script's DOCUMENT_ID type adds .did.
            backendApiConditions.push({
                type: 'DOCUMENT_ID',
                data: { doc_id: googleLikeFields.documentId.trim().replace(/patent\//i, '') }
            });
        }

        // Prepare payload for the backend
        const payload = {
            conditions: backendApiConditions.filter(c => c && c.data && (c.data.text || c.data.name || c.data.value || c.data.expression || c.data.doc_id)),
            databases: usptoSelectedDatabases,
            combine_conditions_with: 'AND' // Default, as different fields are usually ANDed
        };
        
        try {
            const response = await fetch('/api/generate-uspto-query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `HTTP error! status: ${response.status}` }));
                console.error("USPTO Query Generation Error:", errorData);
                queryResult = { queryStringDisplay: errorData.error || `Error: ${response.statusText}`, url: '#' };
            } else {
                const result = await response.json();
                queryResult = { queryStringDisplay: result.query_string_display || '', url: result.url || '#' };
            }
        } catch (error) {
            console.error("Failed to fetch USPTO query:", error);
            queryResult = { queryStringDisplay: error instanceof Error ? error.message : "Network error for USPTO query", url: "#" };
        }
    }
    onMainInputChange(queryResult.queryStringDisplay);
    const isValidQuery = queryResult.queryStringDisplay.trim() &&
                         !queryResult.queryStringDisplay.startsWith("Error") &&
                         queryResult.url !== '#';
    setQueryLinkHref(isValidQuery ? queryResult.url : '#');
  }, [activeFormat, searchConditions, googleLikeFields, onMainInputChange,
      usptoDefaultOperator, /* usptoPlurals, usptoBritishEquivalents, */ usptoSelectedDatabases]); // Removed plurals/british from deps as backend doesn't use them yet for SET commands

  useEffect(() => {
    if (activeFormat === 'uspto') {
        if (searchConditions.length === 0 || searchConditions[0].type !== 'TEXT') {
            setSearchConditions([createDefaultTextCondition()]);
        } else if (searchConditions.length > 1) {
            setSearchConditions([searchConditions[0]]);
        }
    }
    assembleQuery(activeFormat);
}, [activeFormat, searchConditions, googleLikeFields, assembleQuery,
    usptoDefaultOperator, usptoPlurals, usptoBritishEquivalents, usptoSelectedDatabases]);

  const renderSearchConditionRow = (condition: SearchCondition, isForNewEntryPlaceholder: boolean, canBeRemoved: boolean): React.ReactNode => {
    if (condition.type === 'TEXT') {
      const textData = condition.data as InternalTextSearchData;
      const isUsptoActive = activeFormat === 'uspto';
      const inputClassName = `w-full p-2 border-none focus:ring-0 text-sm bg-transparent outline-none ${isUsptoActive ? 'min-h-[160px] resize-y align-top' : ''}`;
      const placeholderText = isUsptoActive
        ? "Enter query text (e.g., electric motor OR TTL/(hybrid vehicle) AND APD/>=1/1/2020)"
        : (isForNewEntryPlaceholder ? "Type here to add search term..." : "Enter search terms...");

      if (isUsptoActive) {
        return (
            <textarea
                value={textData.text}
                onChange={(e) => updateSearchConditionText(condition.id, e.target.value)}
                placeholder={placeholderText}
                className={inputClassName}
                rows={5}
            />
        );
      }
      return (
        <div className="flex items-center w-full">
          <input
            type="text"
            value={textData.text}
            onChange={(e) => updateSearchConditionText(condition.id, e.target.value)}
            placeholder={placeholderText}
            className={inputClassName}
          />
          {canBeRemoved && (<button onClick={() => removeSearchCondition(condition.id)} className="p-1 text-gray-400 hover:text-red-500 focus:outline-none mr-1 flex-shrink-0" title="Remove search condition"><XCircle size={16} /></button>)}
        </div>
      );
    }

    let displayText = `${condition.type.charAt(0).toUpperCase() + condition.type.slice(1).toLowerCase()}: `;
     switch (condition.type) {
        case 'CLASSIFICATION':
            const cpcData = condition.data;
            displayText += `${cpcData.cpc || "N/A"} (${cpcData.option === 'CHILDREN' ? 'incl. children' : 'exact'})`;
            break;
        case 'CHEMISTRY':
            const chemData = condition.data;
            displayText += `${chemData.term ? `"${chemData.term}"` : "N/A"} (${chemData.uiOperatorLabel}, ${chemData.docScope})`;
            break;
        case 'MEASURE':
            const measureData = condition.data;
            const measurePart = measureData.measurements ? `"${measureData.measurements}"` : "N/A";
            const unitsPart = measureData.units_concepts ? ` for "${measureData.units_concepts}"` : "";
            displayText += `${measurePart}${unitsPart}`;
            if (measureData.measurements.trim() === "" && measureData.units_concepts.trim() === "") {
                displayText = `Measure: N/A`;
            }
            break;
        case 'NUMBERS':
            const numData = condition.data;
            const firstDocId = numData.doc_ids_text.split('\n')[0].trim();
            const hasMoreIds = numData.doc_ids_text.includes('\n');
            let numDisplayText = `Docs: ${firstDocId || "N/A"}${hasMoreIds ? "..." : ""}`;
            if (numData.number_type !== 'EITHER') {
                numDisplayText += ` (${numData.number_type.substring(0,3).toLowerCase()})`;
            }
            if (numData.country_restriction) {
                numDisplayText += ` [${numData.country_restriction}]`;
            }
            if (numData.preferred_countries_order) {
                 numDisplayText += ` (pref: ${numData.preferred_countries_order.substring(0,10)}${numData.preferred_countries_order.length > 10 ? '...' : ''})`;
            }
            displayText = numDisplayText;
            break;
        default:
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const _exhaustiveCheck: never = condition;
            console.error(`Unhandled SearchCondition type in renderSearchConditionRow (displayText): ${(condition as any).type}`);
            displayText = `Unknown Tool (${(condition as any).type.toString()}): Click to configure`;
    }
    return (
        <div className="flex items-center justify-between w-full">
            <span className="text-sm p-2 flex-grow truncate" title={displayText}>{displayText}</span>
            {canBeRemoved && (<button onClick={() => removeSearchCondition(condition.id)} className="p-1 text-gray-400 hover:text-red-500 focus:outline-none mr-1 flex-shrink-0" title="Remove search condition"><XCircle size={16} /></button>)}
        </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="text-center"><h2 className="text-2xl font-semibold text-gray-800">Patent Query Tool</h2></div>
      <div className="flex border-b border-gray-200">
        {formatTabs.map(tab => <button key={tab.value} onClick={() => handleTabClick(tab.value)} className={`flex items-center justify-center px-4 py-3 -mb-px text-sm font-medium focus:outline-none transition-colors duration-150 ${activeFormat === tab.value ? 'border-b-2 border-blue-600 text-blue-600' : 'border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>{tab.icon}{tab.label}</button>)}
      </div>

      {activeFormat !== 'uspto' && ( // Keep this for Google Patents URL
        <div className="space-y-1 pt-4">
          <a
            href={queryLinkHref}
            target="_blank"
            rel="noopener noreferrer"
            className={`block text-sm font-medium mb-1 text-center ${queryLinkHref !== '#' ? 'text-blue-600 hover:text-blue-800 hover:underline cursor-pointer' : 'text-gray-700 cursor-default'}`}
            onClick={(e) => { if (queryLinkHref === '#') e.preventDefault(); }}
          >
            Search Query {queryLinkHref !== '#' && <LinkIcon className="inline-block h-3 w-3 ml-1 mb-0.5" />}
          </a>
          <input id="mainQueryInput" type="text" value={mainQueryValue} onChange={handleMainQueryDirectInputChange} placeholder={`Assembled query...`} className={`block w-full rounded-lg border bg-slate-50 px-4 py-3 text-slate-800 placeholder-slate-400 text-base shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-shadow duration-150 ease-in-out ${mainQueryValue.startsWith("Error") ? 'border-red-500 text-red-700' : (mainQueryValue.trim() === '' && queryLinkHref === '#' ? 'border-gray-300' : 'border-blue-300')}`}/>
        </div>
      )}

      <div className="pt-4 border-t border-gray-200">
        <div className={`mb-3 ${activeFormat === 'uspto' ? 'text-center' : 'flex justify-between items-center'}`}>
            {activeFormat === 'uspto' ? (
                <>
                 <a
                    href={queryLinkHref} // This will now be set by the backend for USPTO too
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`inline-flex items-center text-sm font-medium ${queryLinkHref !== '#' ? 'text-blue-600 hover:text-blue-800 hover:underline cursor-pointer' : 'text-gray-500 cursor-default'}`}
                    onClick={(e) => { if (queryLinkHref === '#') e.preventDefault(); }}
                    title={queryLinkHref !== '#' ? `Open USPTO Advanced Search with current query` : 'Query not yet valid or assembled for search'}
                 >
                    Search Query
                    {queryLinkHref !== '#' && <LinkIcon className="inline-block h-3 w-3 ml-1.5 mb-0.5" />}
                 </a>
                 {/* Display the assembled query string for USPTO as well */}
                 <input 
                    id="usptoMainQueryDisplay" 
                    type="text" 
                    value={mainQueryValue} 
                    readOnly 
                    placeholder="Assembled USPTO query..." 
                    className={`block w-full rounded-lg border bg-slate-50 px-4 py-3 text-slate-800 placeholder-slate-400 text-sm shadow-sm mt-2 text-center ${mainQueryValue.startsWith("Error") ? 'border-red-500 text-red-700' : (mainQueryValue.trim() === '' && queryLinkHref === '#' ? 'border-gray-300' : 'border-blue-300')}`}
                 />
                </>
            ) : (
                <h3 className="text-lg font-medium text-gray-700 flex items-center">
                    <Wand2 className="h-5 w-5 mr-2 text-blue-600" />
                    Search Terms
                </h3>
            )}
        </div>

        <div className={`p-4 border border-gray-200 rounded-lg space-y-3 bg-gray-50 shadow ${activeFormat === 'uspto' ? 'min-h-[200px] flex' : ''}`}>
          {searchConditions.map((condition: SearchCondition, index: number) => {
            if (activeFormat === 'uspto' && (condition.type !== 'TEXT' || index > 0)) {
              return null;
            }
            const isLastCondition = index === searchConditions.length - 1;
            const isTextCondition = condition.type === 'TEXT';
            const textData = isTextCondition ? (condition.data as InternalTextSearchData) : { text: '', selectedScopes: new Set(['FT']), termOperator: 'ALL' };
            const isForNewEntryPlaceholder = activeFormat !== 'uspto' && isLastCondition && isTextCondition && textData.text.trim() === '';

            const canBeRemoved = activeFormat !== 'uspto' && (
                searchConditions.length > 1 ||
                (condition.type !== 'TEXT') ||
                (condition.type === 'TEXT' && textData.text.trim() !== '')
            );
            return (
                <div key={condition.id} className={`border border-gray-300 rounded-md bg-white shadow-sm flex items-stretch ${activeFormat === 'uspto' ? 'flex-grow' : ''}`}>
                  <div className={`flex-grow min-w-0 ${activeFormat !== 'uspto' ? 'border-r border-gray-300' : ''} ${activeFormat === 'uspto' ? 'w-full' : ''}`}>
                      {renderSearchConditionRow(condition, isForNewEntryPlaceholder, canBeRemoved)}
                  </div>
                  {activeFormat !== 'uspto' && (
                    <button
                        onClick={() => handleOpenSearchToolModal(condition)}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-r-md flex items-center justify-center focus:outline-none focus:ring-1 focus:ring-blue-500 flex-shrink-0"
                        title={`Change tool type (current: ${condition.type})`}
                        style={{ minWidth: '40px' }}
                    >
                        {getConditionTypeIcon(condition.type)}
                    </button>
                  )}
                </div>
            );
          })}
        </div>
      </div>
      <div className="pt-4 border-t border-gray-200">
        <h3 className="text-lg font-medium text-gray-700 mb-3">
            {activeFormat === 'uspto' ? 'Query Settings' : 'Search Fields'}
        </h3>
        {activeFormat === 'google' && (
            <GooglePatentsFields
                fields={googleLikeFields}
                onFieldChange={handleGoogleLikeFieldChange}
                onPatentOfficeToggle={handlePatentOfficeToggle}
                onLanguageToggle={handleLanguageToggle}
                onAddDynamicEntry={addDynamicFieldEntry}
                onRemoveDynamicEntry={removeDynamicFieldEntry}
                currentInventorInput={currentInventorInput}
                setCurrentInventorInput={setCurrentInventorInput}
                currentAssigneeInput={currentAssigneeInput}
                setCurrentAssigneeInput={setCurrentAssigneeInput}
                inventorInputRef={inventorInputRef}
                assigneeInputRef={assigneeInputRef}
                isPatentOfficeDropdownOpen={isPatentOfficeDropdownOpen}
                setIsPatentOfficeDropdownOpen={setIsPatentOfficeDropdownOpen}
                isLanguageDropdownOpen={isLanguageDropdownOpen}
                setIsLanguageDropdownOpen={setIsLanguageDropdownOpen}
                patentOfficeRef={patentOfficeRef}
                languageRef={languageRef}
            />
        )}
        {activeFormat === 'uspto' && (
            <UsptoPatentsFields
                defaultOperator={usptoDefaultOperator}
                setDefaultOperator={setUsptoDefaultOperator}
                highlights={usptoHighlights}
                setHighlights={setUsptoHighlights}
                showErrors={usptoShowErrors}
                setShowErrors={setUsptoShowErrors}
                plurals={usptoPlurals}
                setPlurals={setUsptoPlurals}
                britishEquivalents={usptoBritishEquivalents}
                setBritishEquivalents={setUsptoBritishEquivalents}
                selectedDatabases={usptoSelectedDatabases}
                setSelectedDatabases={setUsptoSelectedDatabases}
                onSearch={() => { // This button will now rely on the queryLinkHref from backend
                    if (queryLinkHref && queryLinkHref !== '#') {
                        window.open(queryLinkHref, '_blank', 'noopener,noreferrer');
                    } else {
                        // Trigger re-assembly if link is not ready
                        assembleQuery('uspto').then(() => {
                            // Small delay to allow state update for queryLinkHref
                            setTimeout(() => {
                                if (queryLinkHref && queryLinkHref !== '#') {
                                     window.open(queryLinkHref, '_blank', 'noopener,noreferrer');
                                } else {
                                    alert("Query is not ready or is invalid. Please check your inputs.");
                                }
                            }, 100);
                        });
                        console.log("Query not ready or invalid for USPTO search via button. Attempting to assemble...");
                    }
                }}
                onClear={() => {
                    if (searchConditions.length > 0 && searchConditions[0].type === 'TEXT') {
                        updateSearchConditionText(searchConditions[0].id, '');
                    }
                    // Clear googleLikeFields as well if they contribute to USPTO query
                    setGoogleLikeFields({
                        dateFrom: '', dateTo: '', dateType: 'publication',
                        inventors: [], assignees: [], patentOffices: [], languages: [],
                        status: '', patentType: '', litigation: '',
                        cpc: '', specificTitle: '', documentId: ''
                    });
                    setUsptoDefaultOperator('OR');
                    setUsptoPlurals(false);
                    setUsptoBritishEquivalents(true);
                    setUsptoSelectedDatabases(['US-PGPUB', 'USPAT', 'USOCR']);
                    // assembleQuery('uspto'); // Trigger re-assembly after clear
                }}
                onPatentNumberSearch={() => {
                     // This could set the documentId field and trigger a query re-assembly
                    const pn = prompt("Enter Patent Number for USPTO search:");
                    if (pn && pn.trim()) {
                        setGoogleLikeFields(prev => ({ ...prev, documentId: pn.trim() }));
                        // assembleQuery('uspto'); // Optionally auto-trigger
                    }
                    console.log("USPTO PN Search clicked - ideally sets documentId field.");
                }}
            />
        )}
      </div>

      {isSearchToolModalOpen && editingCondition && activeFormat !== 'uspto' && (
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
// --- END OF FILE ChatInput.tsx ---
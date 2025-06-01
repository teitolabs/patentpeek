// src/components/ChatInput.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { PatentFormat } from '../types';
import {
    // Building2, // Correctly used in formatTabs
    XCircle, Filter, Settings2, Type as TypeIcon, Wand2, Link as LinkIcon,
    FlaskConical, Ruler, Hash, Building2 as Building2Icon // Use alias for clarity if needed
} from 'lucide-react';
import SearchToolModal, { ModalToolData } from './SearchToolModal';
import {
    SearchCondition, SearchToolType, TextSearchCondition, InternalTextSearchData,
    PatentOffice, Language, DateType
} from './searchToolTypes';

import GooglePatentsFields, { GoogleLikeSearchFields } from './googlePatents/GooglePatentsFields';
import { generateGoogleQuery } from './googlePatents/googleQueryBuilder';
import UsptoPatentsFields from './usptoPatents/UsptoPatentsFields';

export interface ChatInputProps {
  value: string; 
  activeFormat: PatentFormat;
  onTabChange: (newFormat: PatentFormat) => void;
  onMainInputChange: (text: string) => void;
}

// GoogleGIcon is used in formatTabs, this is fine.
function GoogleGIcon(): React.ReactElement { return (<svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M12.2446 10.925L12.2446 14.005L18.7746 14.005C18.5346 15.095 18.0546 16.125 17.3446 16.965C16.5846 17.855 15.2746 18.665 13.4846 18.665C10.6846 18.665 8.31462 16.375 8.31462 13.495C8.31462 10.615 10.6846 8.32502 13.4846 8.32502C14.9346 8.32502 16.0046 8.92502 16.9546 9.81502L19.1146 7.71502C17.6746 6.38502 15.8046 5.32502 13.4846 5.32502C9.86462 5.32502 6.91462 8.22502 6.91462 11.995C6.91462 15.765 9.86462 18.665 13.4846 18.665C15.9146 18.665 17.7246 17.835 19.0646 16.415C20.4746 14.925 20.9846 12.925 20.9846 11.495C20.9846 10.925 20.9446 10.475 20.8546 10.005L13.4846 10.005L12.2446 10.925Z" /></svg>);}

function getConditionTypeIcon(type: SearchToolType): React.ReactElement { 
    switch(type) {
        case 'TEXT': return <TypeIcon size={18} className="text-gray-600" />;
        case 'CLASSIFICATION': return <Filter size={18} className="text-gray-600" />;
        case 'CHEMISTRY': return <FlaskConical size={18} className="text-orange-600" />;
        case 'MEASURE': return <Ruler size={18} className="text-purple-600" />;
        case 'NUMBERS': return <Hash size={18} className="text-teal-600" />;
        default:
            console.error("Unhandled SearchToolType in getConditionTypeIcon:", type);
            return <Settings2 size={18} className="text-gray-600" />;
    }
}

// Building2Icon is used here, so the import for Building2Icon is correct.
const formatTabs: Array<{ value: PatentFormat; label: string; icon: React.ReactNode }> = [
  { value: 'google', label: 'Google Patents', icon: <GoogleGIcon /> },
  { value: 'uspto', label: 'USPTO', icon: <Building2Icon className="h-5 w-5 mr-2" /> },
];

const mapDateTypeToUSPTO_local = (dt: DateType): string => { 
    if(dt === 'filing') return 'AD';
    if(dt === 'priority') return 'PRD';
    return 'PD';
}
const formatDateForUSPTO_local = (dateStr: string): string => { 
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-');
    if (!year || !month || !day || year.length !== 4 || month.length !== 2 || day.length !== 2) {
        console.warn(`Invalid date string for USPTO formatting: ${dateStr}`);
        return '';
    }
    return `${parseInt(month, 10)}/${parseInt(day, 10)}/${year}`;
}


const ChatInput: React.FC<ChatInputProps> = ({
  value: mainQueryValue, activeFormat, onTabChange, onMainInputChange,
}) => {
  const createDefaultTextCondition = useCallback((): TextSearchCondition => ({
    id: crypto.randomUUID(),
    type: 'TEXT',
    data: { text: '', selectedScopes: new Set(['FT']), termOperator: 'ALL' }
  }), []);

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

  const [usptoDefaultOperator, setUsptoDefaultOperator] = useState<string>('AND');
  const [usptoHighlights, setUsptoHighlights] = useState<string>('SINGLE_COLOR');
  const [usptoShowErrors, setUsptoShowErrors] = useState<boolean>(true);
  const [usptoPlurals, setUsptoPlurals] = useState<boolean>(false);
  const [usptoBritishEquivalents, setUsptoBritishEquivalents] = useState<boolean>(true);
  const [usptoSelectedDatabases, setUsptoSelectedDatabases] = useState<string[]>(['US-PGPUB', 'USPAT', 'USOCR']);


  useEffect(() => { 
    function handleClickOutside(event: MouseEvent) {
      if (patentOfficeRef.current && !patentOfficeRef.current.contains(event.target as Node)) setIsPatentOfficeDropdownOpen(false);
      if (languageRef.current && !languageRef.current.contains(event.target as Node)) setIsLanguageDropdownOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMainQueryDirectInputChange = (e: React.ChangeEvent<HTMLInputElement>) => onMainInputChange(e.target.value);
  const handleTabClick = (newFormat: PatentFormat) => onTabChange(newFormat);

  useEffect(() => {
    if (activeFormat === 'uspto') {
        const currentText = searchConditions.length > 0 && searchConditions[0].type === 'TEXT' ? (searchConditions[0].data as InternalTextSearchData).text : '';
        if (currentText !== mainQueryValue) {
            const newUsptoTextCond = createDefaultTextCondition();
            newUsptoTextCond.data.text = mainQueryValue;
            setSearchConditions([newUsptoTextCond]);
        }
    } else { 
        const firstTextCondIndex = searchConditions.findIndex(sc => sc.type === 'TEXT');
        
        if (firstTextCondIndex !== -1) { 
            const textCond = searchConditions[firstTextCondIndex] as TextSearchCondition;
            if (textCond.data.text !== mainQueryValue) {
                const newConditions = [...searchConditions];
                (newConditions[firstTextCondIndex].data as InternalTextSearchData).text = mainQueryValue;
                setSearchConditions(newConditions);
            }
        } else { 
            const newTextCond = createDefaultTextCondition();
            newTextCond.data.text = mainQueryValue;
            setSearchConditions([newTextCond, ...searchConditions]);
        }
    }
  }, [activeFormat, mainQueryValue, createDefaultTextCondition, searchConditions]); // Added searchConditions here because it's read


  const handleOpenSearchToolModal = (conditionToEdit: SearchCondition) => { setEditingCondition(conditionToEdit); setIsSearchToolModalOpen(true); };
  const handleCloseSearchToolModal = () => { setIsSearchToolModalOpen(false); setEditingCondition(undefined); };
  const handleUpdateSearchConditionFromModal = (conditionId: string, newType: SearchToolType, newData: ModalToolData) => { 
    setSearchConditions(prev =>
      prev.map(sc => sc.id === conditionId ? { ...sc, type: newType, data: newData as any } : sc)
    );
    handleCloseSearchToolModal();
  };

  const removeSearchCondition = (id: string) => {
    setSearchConditions(prev => {
        if (activeFormat === 'uspto' && prev.length === 1 && prev[0].id === id && prev[0].type === 'TEXT') {
            return [{ ...prev[0], data: { ...(prev[0].data as InternalTextSearchData), text: '' } }]; 
        }
        let newConditions = prev.filter(sc => sc.id !== id);
        if (activeFormat !== 'uspto') {
            if (newConditions.length === 0 || !newConditions.some(c => c.type === 'TEXT')) {
                newConditions.unshift(createDefaultTextCondition()); 
            }
            const lastCond = newConditions[newConditions.length - 1];
            if (lastCond.type === 'TEXT' && (lastCond.data as InternalTextSearchData).text.trim() !== '') {
                 if (!newConditions.find((c, i) => i > 0 && c.id !== lastCond.id && c.type === 'TEXT' && (c.data as InternalTextSearchData).text.trim() === '')) {
                    newConditions.push(createDefaultTextCondition()); 
                 }
            }
        } else { 
             if (newConditions.length === 0) newConditions = [createDefaultTextCondition()]; 
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
          // const isCurrentTextEmpty = textData.text.trim() === ''; // This was unused

          if (isCurrentTextFilled && conditionIndex === updatedConditions.length - 1) {
            updatedConditions.push(createDefaultTextCondition()); 
          }
        }
        if (!updatedConditions.some(c=> c.type === 'TEXT')) { 
          updatedConditions.unshift(createDefaultTextCondition());
        }
      }
      return updatedConditions;
    });
  };

  const handleGoogleLikeFieldChange = <K extends keyof GoogleLikeSearchFields>(field: K, value: GoogleLikeSearchFields[K]) => setGoogleLikeFields(prev => ({ ...prev, [field]: value }));
  const handlePatentOfficeToggle = (officeCode: PatentOffice) => setGoogleLikeFields(prev => ({ ...prev, patentOffices: prev.patentOffices.includes(officeCode) ? prev.patentOffices.filter(po => po !== officeCode) : [...prev.patentOffices, officeCode] }));
  const handleLanguageToggle = (langCode: Language) => setGoogleLikeFields(prev => ({ ...prev, languages: prev.languages.includes(langCode) ? prev.languages.filter(lang => lang !== langCode) : [...prev.languages, langCode] }));
  const addDynamicFieldEntry = (field: 'inventors' | 'assignees') => { 
    const currentInput = field === 'inventors' ? currentInventorInput : currentAssigneeInput;
    const setCurrentInput = field === 'inventors' ? setCurrentInventorInput : setCurrentAssigneeInput;
    const inputRef = field === 'inventors' ? inventorInputRef : assigneeInputRef;
    if (currentInput.trim()) {
      setGoogleLikeFields(prev => ({...prev, [field]: [...prev[field], { id: crypto.randomUUID(), value: currentInput.trim() }]}));
      setCurrentInput(''); inputRef.current?.focus();
    }
  };
  const removeDynamicFieldEntry = (field: 'inventors' | 'assignees', id: string) => setGoogleLikeFields(prev => ({...prev, [field]: prev[field].filter(entry => entry.id !== id)}));

  const assembleQueryRaw = useCallback(async (formatToUse: PatentFormat, conditions: SearchCondition[], commonFields: GoogleLikeSearchFields, usptoOp: string, usptoDBs: string[]) => {
    if (formatToUse === 'google') {
      return generateGoogleQuery(conditions, commonFields);
    } else if (formatToUse === 'uspto') {
        const backendApiConditions: any[] = [];
        const usptoSearchTextCondition = conditions.find(sc => sc.type === 'TEXT') as TextSearchCondition | undefined;
        const usptoSearchText = usptoSearchTextCondition ? usptoSearchTextCondition.data.text : '';

        if (usptoSearchText.trim()) {
            backendApiConditions.push({
            type: 'TEXT',
            data: { text: usptoSearchText.trim(), field: 'ALL', multi_word_op: usptoOp, is_exact: false }
            });
        }
        if (commonFields.inventors.length > 0) { commonFields.inventors.forEach(inv => { if (inv.value.trim()) backendApiConditions.push({ type: 'INVENTOR', data: { name: inv.value.trim(), multi_word_op: 'ADJ' }}); }); }
        if (commonFields.assignees.length > 0) { commonFields.assignees.forEach(asg => { if (asg.value.trim()) backendApiConditions.push({ type: 'ASSIGNEE', data: { name: asg.value.trim(), multi_word_op: 'ADJ' } }); });}
        if (commonFields.dateFrom) { const fd = formatDateForUSPTO_local(commonFields.dateFrom); if (fd) backendApiConditions.push({ type: 'DATE', data: { field: mapDateTypeToUSPTO_local(commonFields.dateType), expression: `>=${fd}` } }); }
        if (commonFields.dateTo) { const fd = formatDateForUSPTO_local(commonFields.dateTo); if (fd) backendApiConditions.push({ type: 'DATE', data: { field: mapDateTypeToUSPTO_local(commonFields.dateType), expression: `<=${fd}` } }); }
        if (commonFields.cpc?.trim()) { backendApiConditions.push({ type: 'CLASSIFICATION', data: { value: commonFields.cpc.trim(), class_type: 'CPC' } }); }
        if (commonFields.specificTitle?.trim()) { backendApiConditions.push({ type: 'TEXT', data: { text: commonFields.specificTitle.trim(), field: 'TI', is_exact: true, multi_word_op: 'ADJ'} }); }
        if (commonFields.documentId?.trim()) { backendApiConditions.push({ type: 'DOCUMENT_ID', data: { doc_id: commonFields.documentId.trim().replace(/patent\//i, '') } }); }
        
        const payload = {
            conditions: backendApiConditions.filter(c => c?.data && (c.data.text || c.data.name || c.data.value || c.data.expression || c.data.doc_id)),
            databases: usptoDBs,
            combine_conditions_with: 'AND' 
        };
        try {
            const response = await fetch('/api/generate-uspto-query', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            if (!response.ok) { const errorData = await response.json().catch(() => ({ error: `HTTP error! status: ${response.status}` })); return { queryStringDisplay: errorData.error || `Error: ${response.statusText}`, url: '#' }; }
            const result = await response.json();
            return { queryStringDisplay: result.query_string_display || '', url: result.url || '#' };
        } catch (error) { return { queryStringDisplay: error instanceof Error ? error.message : "Network error for USPTO query", url: "#" }; }
    }
    return { queryStringDisplay: 'Unknown format', url: '#' };
  }, []); 


  useEffect(() => {
    let isMounted = true;
    const performAssembly = async () => {
        const result = await assembleQueryRaw(activeFormat, searchConditions, googleLikeFields, usptoDefaultOperator, usptoSelectedDatabases);
        if (isMounted) {
            onMainInputChange(result.queryStringDisplay); 
            const isValidQuery = result.queryStringDisplay.trim() &&
                                 !result.queryStringDisplay.startsWith("Error") &&
                                 !result.queryStringDisplay.startsWith("API Error") &&
                                 !result.queryStringDisplay.startsWith("Network error") &&
                                 result.url !== '#';
            setQueryLinkHref(isValidQuery ? result.url : '#');
        }
    };
    performAssembly();
    return () => { isMounted = false; };
  }, [activeFormat, searchConditions, googleLikeFields, usptoDefaultOperator, usptoSelectedDatabases, assembleQueryRaw, onMainInputChange]);


  const renderSearchConditionRow = (condition: SearchCondition, isForNewEntryPlaceholder: boolean, canBeRemoved: boolean): React.ReactNode => { 
    if (condition.type === 'TEXT') {
      const textData = condition.data as InternalTextSearchData;
      const isUsptoActive = activeFormat === 'uspto';
      const inputClassName = `w-full p-2 border-none focus:ring-0 text-sm bg-transparent outline-none ${isUsptoActive ? 'min-h-[160px] resize-y align-top' : ''}`;
      const placeholderText = isUsptoActive
        ? "Enter query text (e.g., electric motor OR TTL/(hybrid vehicle) AND APD/>=1/1/2020)"
        : (isForNewEntryPlaceholder ? "Type here to add search term..." : "Enter search terms...");

      if (isUsptoActive) {
        return ( <textarea value={textData.text} onChange={(e) => updateSearchConditionText(condition.id, e.target.value)} placeholder={placeholderText} className={inputClassName} rows={5} /> );
      }
      return ( <div className="flex items-center w-full"> <input type="text" value={textData.text} onChange={(e) => updateSearchConditionText(condition.id, e.target.value)} placeholder={placeholderText} className={inputClassName} /> {canBeRemoved && (<button onClick={() => removeSearchCondition(condition.id)} className="p-1 text-gray-400 hover:text-red-500 focus:outline-none mr-1 flex-shrink-0" title="Remove search condition"><XCircle size={16} /></button>)} </div> );
    }
    let displayText = `${condition.type.charAt(0).toUpperCase() + condition.type.slice(1).toLowerCase()}: `;
     switch (condition.type) {
        case 'CLASSIFICATION': const cpcData = condition.data; displayText += `${cpcData.cpc || "N/A"} (${cpcData.option === 'CHILDREN' ? 'incl. children' : 'exact'})`; break;
        case 'CHEMISTRY': const chemData = condition.data; displayText += `${chemData.term ? `"${chemData.term}"` : "N/A"} (${chemData.uiOperatorLabel}, ${chemData.docScope})`; break;
        case 'MEASURE': const md = condition.data; displayText += `${md.measurements ? `"${md.measurements}"` : "N/A"}${md.units_concepts ? ` for "${md.units_concepts}"` : ""}`; if (md.measurements.trim()==="" && md.units_concepts.trim()==="") displayText=`Measure: N/A`; break;
        case 'NUMBERS': const nd = condition.data; const fId = nd.doc_ids_text.split('\n')[0].trim(); let numDT = `Docs: ${fId||"N/A"}${nd.doc_ids_text.includes('\n')?"...":""}`; if(nd.number_type!=='EITHER') numDT+=` (${nd.number_type.substring(0,3).toLowerCase()})`; if(nd.country_restriction) numDT+=` [${nd.country_restriction}]`; if(nd.preferred_countries_order) numDT+=` (pref: ${nd.preferred_countries_order.substring(0,10)}${nd.preferred_countries_order.length>10?'...':''})`; displayText=numDT; break;
        default: console.error(`Unhandled SearchCondition type: ${(condition as any).type}`); displayText = `Unknown Tool: Click to configure`;
    }
    return ( <div className="flex items-center justify-between w-full"> <span className="text-sm p-2 flex-grow truncate" title={displayText}>{displayText}</span> {canBeRemoved && (<button onClick={() => removeSearchCondition(condition.id)} className="p-1 text-gray-400 hover:text-red-500 focus:outline-none mr-1 flex-shrink-0" title="Remove search condition"><XCircle size={16} /></button>)} </div> );
  };

  return (
    <div className="space-y-6">
      <div className="text-center"><h2 className="text-2xl font-semibold text-gray-800">Patent Query Tool</h2></div>
      <div className="flex border-b border-gray-200">
        {formatTabs.map(tab => <button key={tab.value} onClick={() => handleTabClick(tab.value)} className={`flex items-center justify-center px-4 py-3 -mb-px text-sm font-medium focus:outline-none transition-colors duration-150 ${activeFormat === tab.value ? 'border-b-2 border-blue-600 text-blue-600' : 'border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>{tab.icon}{tab.label}</button>)}
      </div>

      <div className="space-y-1 pt-4">
        <a href={queryLinkHref} target="_blank" rel="noopener noreferrer" className={`block text-sm font-medium mb-1 text-center ${queryLinkHref !== '#' ? 'text-blue-600 hover:text-blue-800 hover:underline cursor-pointer' : 'text-gray-700 cursor-default'}`} onClick={(e) => { if (queryLinkHref === '#') e.preventDefault(); }} title={queryLinkHref !== '#' ? `Open ${activeFormat === 'google' ? 'Google Patents' : 'USPTO Advanced Search'} with current query` : 'Query not yet valid or assembled for search'}>
          Search Query {queryLinkHref !== '#' && <LinkIcon className="inline-block h-3 w-3 ml-1 mb-0.5" />}
        </a>
        <input id="mainQueryInputDisplay" type="text" value={mainQueryValue} onChange={handleMainQueryDirectInputChange} placeholder="Assembled query..." className={`block w-full rounded-lg border bg-slate-50 px-4 py-3 text-slate-800 placeholder-slate-400 text-base shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-shadow duration-150 ease-in-out ${mainQueryValue.startsWith("Error") || mainQueryValue.startsWith("API Error") || mainQueryValue.startsWith("Network error") ? 'border-red-500 text-red-700' : (mainQueryValue.trim() === '' && queryLinkHref === '#' ? 'border-gray-300' : 'border-blue-300')}`} />
      </div>

      <div className="pt-4 border-t border-gray-200">
        <div className={`mb-3 ${activeFormat === 'uspto' ? 'text-center' : 'flex justify-between items-center'}`}>
            {activeFormat === 'uspto' ? ( <h3 className="text-lg font-medium text-gray-700 flex items-center justify-center"> <Wand2 className="h-5 w-5 mr-2 text-blue-600" /> USPTO Query Builder </h3> ) : ( <h3 className="text-lg font-medium text-gray-700 flex items-center"> <Wand2 className="h-5 w-5 mr-2 text-blue-600" /> Search Terms </h3> )}
        </div>
        <div className={`p-4 border border-gray-200 rounded-lg space-y-3 bg-gray-50 shadow ${activeFormat === 'uspto' ? 'min-h-[200px] flex' : ''}`}>
          {searchConditions.map((condition: SearchCondition, index: number) => {
            if (activeFormat === 'uspto' && (condition.type !== 'TEXT' || index > 0)) return null; 
            const isLastCondition = index === searchConditions.length - 1;
            const isTextCondition = condition.type === 'TEXT';
            const textData = isTextCondition ? (condition.data as InternalTextSearchData) : { text: '', selectedScopes: new Set(['FT']), termOperator: 'ALL' };
            const isForNewEntryPlaceholder = activeFormat !== 'uspto' && isLastCondition && isTextCondition && textData.text.trim() === '';
            const canBeRemoved = activeFormat !== 'uspto' && ( searchConditions.length > 1 || (condition.type !== 'TEXT') || (condition.type === 'TEXT' && textData.text.trim() !== '') );
            return ( <div key={condition.id} className={`border border-gray-300 rounded-md bg-white shadow-sm flex items-stretch ${activeFormat === 'uspto' ? 'flex-grow w-full' : ''}`}> <div className={`flex-grow min-w-0 ${activeFormat !== 'uspto' ? 'border-r border-gray-300' : ''} ${activeFormat === 'uspto' ? 'w-full' : ''}`}> {renderSearchConditionRow(condition, isForNewEntryPlaceholder, canBeRemoved)} </div> {activeFormat !== 'uspto' && ( <button onClick={() => handleOpenSearchToolModal(condition)} className="p-2 text-gray-600 hover:bg-gray-100 rounded-r-md flex items-center justify-center focus:outline-none focus:ring-1 focus:ring-blue-500 flex-shrink-0" title={`Change tool type (current: ${condition.type})`} style={{ minWidth: '40px' }}> {getConditionTypeIcon(condition.type)} </button> )} </div> );
          })}
        </div>
      </div>
      <div className="pt-4 border-t border-gray-200">
        <h3 className="text-lg font-medium text-gray-700 mb-3"> {activeFormat === 'uspto' ? 'Query Settings & Common Fields' : 'Search Fields'} </h3>
        {activeFormat === 'google' && ( <GooglePatentsFields fields={googleLikeFields} onFieldChange={handleGoogleLikeFieldChange} onPatentOfficeToggle={handlePatentOfficeToggle} onLanguageToggle={handleLanguageToggle} onAddDynamicEntry={addDynamicFieldEntry} onRemoveDynamicEntry={removeDynamicFieldEntry} currentInventorInput={currentInventorInput} setCurrentInventorInput={setCurrentInventorInput} currentAssigneeInput={currentAssigneeInput} setCurrentAssigneeInput={setCurrentAssigneeInput} inventorInputRef={inventorInputRef} assigneeInputRef={assigneeInputRef} isPatentOfficeDropdownOpen={isPatentOfficeDropdownOpen} setIsPatentOfficeDropdownOpen={setIsPatentOfficeDropdownOpen} isLanguageDropdownOpen={isLanguageDropdownOpen} setIsLanguageDropdownOpen={setIsLanguageDropdownOpen} patentOfficeRef={patentOfficeRef} languageRef={languageRef} /> )}
        {activeFormat === 'uspto' && ( <UsptoPatentsFields 
            defaultOperator={usptoDefaultOperator} setDefaultOperator={setUsptoDefaultOperator} 
            highlights={usptoHighlights} setHighlights={setUsptoHighlights} 
            showErrors={usptoShowErrors} setShowErrors={setUsptoShowErrors} 
            plurals={usptoPlurals} setPlurals={setUsptoPlurals} 
            britishEquivalents={usptoBritishEquivalents} setBritishEquivalents={setUsptoBritishEquivalents} 
            selectedDatabases={usptoSelectedDatabases} setSelectedDatabases={setUsptoSelectedDatabases} // FIX: Pass the correct setter
            onSearch={() => { if (queryLinkHref && queryLinkHref !== '#') { window.open(queryLinkHref, '_blank', 'noopener,noreferrer'); } else { alert("Query is not ready or is invalid. Please check your inputs or wait for assembly."); } }} 
            onClear={() => { if (searchConditions.length > 0 && searchConditions[0].type === 'TEXT') updateSearchConditionText(searchConditions[0].id, ''); setGoogleLikeFields({ dateFrom: '', dateTo: '', dateType: 'publication', inventors: [], assignees: [], patentOffices: [], languages: [], status: '', patentType: '', litigation: '', cpc: '', specificTitle: '', documentId: '' }); setUsptoDefaultOperator('AND'); setUsptoPlurals(false); setUsptoBritishEquivalents(true); setUsptoSelectedDatabases(['US-PGPUB', 'USPAT', 'USOCR']); }} 
            onPatentNumberSearch={() => { const pn = prompt("Enter Patent Number for USPTO search (will be added to common fields):"); if (pn && pn.trim()) setGoogleLikeFields(prev => ({ ...prev, documentId: pn.trim() })); }} 
        /> )}
      </div>
      {isSearchToolModalOpen && editingCondition && activeFormat !== 'uspto' && ( <SearchToolModal isOpen={isSearchToolModalOpen} onClose={handleCloseSearchToolModal} onUpdateCondition={handleUpdateSearchConditionFromModal} initialCondition={editingCondition} /> )}
    </div>
  );
};
export default ChatInput;
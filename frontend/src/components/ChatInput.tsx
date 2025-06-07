// src/components/ChatInput.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { PatentFormat } from '../types';
import {
    XCircle, Type as TypeIcon, Wand2, Link as LinkIcon,
    FlaskConical, Ruler, Hash, Building2 as Building2Icon,
    AlertCircle
} from 'lucide-react';
import SearchToolModal, { ModalToolData } from './SearchToolModal';
import {
    SearchCondition, SearchToolType, TextSearchCondition, InternalTextSearchData,
    PatentOffice, Language, QueryScope
} from './searchToolTypes';

import GooglePatentsFields, { GoogleLikeSearchFields } from './googlePatents/GooglePatentsFields';
import { UsptoSpecificSettings } from './usptoPatents/usptoQueryBuilder';
import { generateQuery, parseQuery } from './googlePatents/googleApi';

const GOOGLE_OPERATORS = /\b(AND|OR|NOT|NEAR\d*|ADJ\d*)\b/gi;

function validateSearchTermText(text: string): string | null {
  const trimmedText = text.trim();
  if (!trimmedText) return null;

  let parenCount = 0;
  for (const char of trimmedText) {
    if (char === '(') parenCount++;
    if (char === ')') parenCount--;
    if (parenCount < 0) return "Unmatched parentheses.";
  }
  if (parenCount !== 0) return "Unmatched parentheses.";

  if ((trimmedText.match(/"/g) || []).length % 2 !== 0) {
    return "Unmatched quotes.";
  }

  const words = trimmedText.replace(/[()"]/g, ' ').split(/\s+/).filter(Boolean);
  if (words.length > 0) {
    const lastWord = words[words.length - 1].toUpperCase();
    if (lastWord.match(GOOGLE_OPERATORS)) {
      return "Query cannot end with an operator.";
    }
  }
  
  if (/\b(AND|OR|NOT)\s+\b(AND|OR|NOT)\b/i.test(trimmedText)) {
      return "Cannot have consecutive operators.";
  }

  return null;
}

export interface ChatInputProps {
  value: string;
  activeFormat: PatentFormat;
  onTabChange: (newFormat: PatentFormat) => void;
  onMainInputChange: (text: string) => void;
}

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  return debouncedValue;
}

function GoogleGIcon(): React.ReactElement { return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21.35 11.1H12.18V13.4H18.2C17.96 15.39 16.48 16.97 14.54 16.97C12.23 16.97 10.36 15.09 10.36 12.78C10.36 10.47 12.23 8.59 14.54 8.59C15.63 8.59 16.59 8.98 17.34 9.68L19.03 8.01C17.65 6.74 16.18 6 14.54 6C10.98 6 8.25 8.73 8.25 12.29C8.25 15.85 10.98 18.58 14.54 18.58C17.63 18.58 19.83 16.59 20.44 13.89H14.54V11.1H21.35Z" fill="#4285F4"/></svg>; }
function getConditionTypeIcon(type: SearchToolType): React.ReactElement { switch (type) { case 'TEXT': return <TypeIcon size={18} />; case 'CLASSIFICATION': return <Hash size={18} />; case 'CHEMISTRY': return <FlaskConical size={18} />; case 'MEASURE': return <Ruler size={18} />; case 'NUMBERS': return <Building2Icon size={18} />; default: return <TypeIcon size={18} />; } }
const formatTabs: Array<{ value: PatentFormat; label: string; icon: React.ReactNode }> = [ { value: 'google', label: 'Google', icon: <GoogleGIcon /> }, { value: 'uspto', label: 'USPTO', icon: <Building2Icon size={18} /> }, ];


const ChatInput: React.FC<ChatInputProps> = ({
  value: mainQueryValue, activeFormat, onTabChange, onMainInputChange,
}) => {
  const createDefaultTextCondition = useCallback((): TextSearchCondition => ({
    id: crypto.randomUUID(), type: 'TEXT', data: { text: '', selectedScopes: new Set(['FT']), termOperator: 'ALL', error: null }
  }), []);

  const [searchConditions, setSearchConditions] = useState<SearchCondition[]>([createDefaultTextCondition()]);
  const [googleLikeFields, setGoogleLikeFields] = useState<GoogleLikeSearchFields>({
    dateFrom: '', dateTo: '', dateType: 'publication', inventors: [], assignees: [], patentOffices: [], languages: [], status: '', patentType: '', litigation: '',
  });
  const [usptoSpecificSettings, setUsptoSpecificSettings] = useState<UsptoSpecificSettings>({
    defaultOperator: 'AND', plurals: false, britishEquivalents: true, selectedDatabases: ['US-PGPUB', 'USPAT', 'USOCR'], highlights: 'SINGLE_COLOR', showErrors: true,
  });
  
  const [queryLinkHref, setQueryLinkHref] = useState<string>('#');
  const isInternalUpdate = useRef(false);
  
  const debouncedQueryForParsing = useDebounce(mainQueryValue, 500);

  const triggerQueryGeneration = useCallback(async () => {
    const hasErrors = searchConditions.some(c => c.type === 'TEXT' && c.data.error);
    if (hasErrors) {
      onMainInputChange('');
      setQueryLinkHref('#');
      return;
    }
    const result = await generateQuery(activeFormat, searchConditions, googleLikeFields, usptoSpecificSettings);
    isInternalUpdate.current = true;
    onMainInputChange(result.queryStringDisplay);
    setQueryLinkHref(result.url);
  }, [activeFormat, searchConditions, googleLikeFields, usptoSpecificSettings, onMainInputChange]);

  useEffect(() => {
    triggerQueryGeneration();
  }, [googleLikeFields, usptoSpecificSettings, activeFormat, triggerQueryGeneration]);

  useEffect(() => {
    if (isInternalUpdate.current) {
        isInternalUpdate.current = false;
        return;
    }
    if (!debouncedQueryForParsing.trim() || debouncedQueryForParsing.startsWith("Google Query from AST")) {
        return;
    }
    const parse = async () => {
        try {
            const result = await parseQuery(activeFormat, debouncedQueryForParsing);
            isInternalUpdate.current = true;
            const newSearchConditions = result.searchConditions.map(sc => {
                if (sc.type === 'TEXT') {
                    const textData = sc.data as unknown as { text: string; selectedScopes: string[]; termOperator: string };
                    return { ...sc, data: { ...textData, selectedScopes: new Set(textData.selectedScopes) as Set<QueryScope>, error: null } };
                }
                return sc;
            });
            setSearchConditions(manageSearchConditionInputs(newSearchConditions as SearchCondition[]));
            setGoogleLikeFields(result.googleLikeFields);
            setUsptoSpecificSettings(result.usptoSpecificSettings);
        } catch (error) {
            console.error("Parsing failed:", error);
            isInternalUpdate.current = true;
            onMainInputChange(`Error parsing query: ${(error as Error).message}`);
        }
    };
    parse();
  }, [debouncedQueryForParsing, activeFormat, createDefaultTextCondition, onMainInputChange]);

  const manageSearchConditionInputs = (conditions: SearchCondition[]): SearchCondition[] => {
    let filteredConditions = conditions.filter((cond, index) => {
        if (cond.type === 'TEXT' && (cond.data as InternalTextSearchData).text.trim() === '') {
            const anotherEmptyExists = conditions.slice(index + 1).some(c => c.type === 'TEXT' && (c.data as InternalTextSearchData).text.trim() === '');
            return !anotherEmptyExists;
        }
        return true;
    });
    const lastCondition = filteredConditions[filteredConditions.length - 1];
    const needsEmptyBox = !lastCondition || lastCondition.type !== 'TEXT' || (lastCondition.data as InternalTextSearchData).text.trim() !== '';
    if (needsEmptyBox) {
        filteredConditions.push(createDefaultTextCondition());
    }
    if(filteredConditions.length === 0) {
        filteredConditions.push(createDefaultTextCondition());
    }
    return filteredConditions;
  };
  
  const handleMainQueryDirectInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    isInternalUpdate.current = false;
    setQueryLinkHref('#');
    onMainInputChange(e.target.value);
  };
  
  const handleTabClick = (newFormat: PatentFormat) => onTabChange(newFormat);
  
  const onFieldChange = <K extends keyof GoogleLikeSearchFields>(field: K, value: GoogleLikeSearchFields[K]) => setGoogleLikeFields(prev => ({ ...prev, [field]: value }));
  
  const handleUpdateSearchConditionFromModal = (conditionId: string, newType: SearchToolType, newData: ModalToolData) => { 
    setSearchConditions(prev => {
        const updated = prev.map(sc => sc.id === conditionId ? { ...sc, type: newType, data: newData as any } : sc);
        triggerQueryGeneration();
        return manageSearchConditionInputs(updated);
    });
    setIsSearchToolModalOpen(false); 
    setEditingCondition(undefined);
  };
  
  const updateSearchConditionText = (id: string, newText: string) => {
      setSearchConditions(prev => {
          const updated = prev.map(sc => {
              if (sc.id === id && sc.type === 'TEXT') {
                  const error = validateSearchTermText(newText);
                  return { ...sc, data: { ...(sc.data as InternalTextSearchData), text: newText, error } };
              }
              return sc;
          });
          return manageSearchConditionInputs(updated);
      });
  };

  const removeSearchCondition = (id: string) => {
      setSearchConditions(prev => {
          const updated = prev.filter(sc => sc.id !== id);
          triggerQueryGeneration();
          return manageSearchConditionInputs(updated);
      });
  };

  const handleTextConditionKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      triggerQueryGeneration();
    }
  };

  const renderSearchConditionRow = (condition: SearchCondition, canBeRemoved: boolean) => {
    const isTextEmpty = condition.type === 'TEXT' && (condition.data as InternalTextSearchData).text.trim() === '';
    
    if (condition.type === 'TEXT') {
      const textData = condition.data as InternalTextSearchData;
      const hasError = !!textData.error;

      return (
        <div className={`flex items-center w-full ${hasError ? 'ring-2 ring-red-500 rounded-md' : ''}`}>
            <input 
              type="text" 
              value={textData.text} 
              onChange={(e) => updateSearchConditionText(condition.id, e.target.value)} 
              onKeyDown={handleTextConditionKeyDown}
              onBlur={triggerQueryGeneration}
              placeholder="Type here to add search term..." 
              className="w-full p-2 border-none focus:ring-0 text-sm bg-transparent outline-none" 
            />
            {hasError && (
              <div className="p-1 text-red-600" title={textData.error!}>
                <AlertCircle size={16} />
              </div>
            )}
            {canBeRemoved && !isTextEmpty && ( <button onClick={() => removeSearchCondition(condition.id)} className="p-1 text-gray-400 hover:text-red-500 focus:outline-none mr-1 flex-shrink-0" title="Remove search condition"><XCircle size={16} /></button> )}
        </div>
      );
    }
    let displayText = `${condition.type.charAt(0).toUpperCase() + condition.type.slice(1).toLowerCase()}: `;
     switch (condition.type) {
        case 'CLASSIFICATION': displayText += `${(condition.data as any).cpc || "N/A"}`; break;
        case 'CHEMISTRY': displayText += `${(condition.data as any).term || "N/A"}`; break;
        case 'MEASURE': displayText += `${(condition.data as any).measurements || "N/A"}`; break;
        case 'NUMBERS': displayText += `${(condition.data as any).doc_ids_text || "N/A"}`; break;
     }
    return (
        <div className="flex items-center justify-between w-full">
            <span className="text-sm p-2 flex-grow truncate" title={displayText}>{displayText}</span>
            {canBeRemoved && ( <button onClick={() => removeSearchCondition(condition.id)} className="p-1 text-gray-400 hover:text-red-500 focus:outline-none mr-1 flex-shrink-0" title="Remove search condition"><XCircle size={16} /></button> )}
        </div>
    );
  };

  const [currentInventorInput, setCurrentInventorInput] = useState('');
  const [currentAssigneeInput, setCurrentAssigneeInput] = useState('');
  const inventorInputRef = useRef<HTMLInputElement>(null);
  const assigneeInputRef = useRef<HTMLInputElement>(null);
  const [isSearchToolModalOpen, setIsSearchToolModalOpen] = useState(false);
  const [editingCondition, setEditingCondition] = useState<SearchCondition | undefined>(undefined);
  const [isPatentOfficeDropdownOpen, setIsPatentOfficeDropdownOpen] = useState(false);
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
  const patentOfficeRef = useRef<HTMLDivElement>(null);
  const languageRef = useRef<HTMLDivElement>(null);
  const onPatentOfficeToggle = (office: PatentOffice) => setGoogleLikeFields(p => ({...p, patentOffices: p.patentOffices.includes(office) ? p.patentOffices.filter(o=>o!==office) : [...p.patentOffices, office]}));
  const onLanguageToggle = (lang: Language) => setGoogleLikeFields(p => ({...p, languages: p.languages.includes(lang) ? p.languages.filter(l=>l!==lang) : [...p.languages, lang]}));
  const onAddDynamicEntry = (field: 'inventors' | 'assignees') => {
    const value = field === 'inventors' ? currentInventorInput.trim() : currentAssigneeInput.trim();
    if (!value) return;
    const newEntry = { id: crypto.randomUUID(), value };
    setGoogleLikeFields(prev => ({ ...prev, [field]: [...prev[field], newEntry] }));
    if (field === 'inventors') setCurrentInventorInput('');
    else setCurrentAssigneeInput('');
  };
  const onRemoveDynamicEntry = (field: 'inventors' | 'assignees', id: string) => {
    setGoogleLikeFields(prev => ({ ...prev, [field]: prev[field].filter(entry => entry.id !== id) }));
  };

  return (
    <div className="space-y-6">
      <div className="text-center"><h2 className="text-2xl font-semibold text-gray-800">Patent Query Tool</h2></div>
      <div className="flex border-b border-gray-200">
        {formatTabs.map(tab => ( <button key={tab.value} onClick={() => handleTabClick(tab.value)} className={`flex items-center gap-2 px-4 py-2 text-sm font-medium focus:outline-none ${activeFormat === tab.value ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}> {tab.icon} {tab.label} </button> ))}
      </div>
      <div className="space-y-1 pt-4">
        <label htmlFor="main-query-input" className="text-sm font-medium text-gray-700">Generated Query String</label>
        <div className="flex items-center border border-gray-300 rounded-lg shadow-sm focus-within:ring-1 focus-within:ring-blue-500 focus-within:border-blue-500">
          <a href={queryLinkHref} target="_blank" rel="noopener noreferrer" className={`p-2 ${queryLinkHref === '#' ? 'cursor-not-allowed text-gray-400' : 'text-blue-600 hover:bg-gray-100'}`} title={queryLinkHref === '#' ? 'Generate a query to enable link' : 'Open query in new tab'} aria-disabled={queryLinkHref === '#'} onClick={(e) => queryLinkHref === '#' && e.preventDefault()}><LinkIcon size={18} /></a>
          <input id="main-query-input" type="text" value={mainQueryValue} onChange={handleMainQueryDirectInputChange} placeholder="Your generated query will appear here..." className="w-full p-2 border-none focus:ring-0 text-sm bg-transparent outline-none" />
        </div>
      </div>
      {activeFormat === 'google' && (
        <>
          <div className="pt-4 border-t border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 flex items-center mb-3"> <Wand2 className="h-5 w-5 mr-2 text-blue-600" /> Search Terms </h3>
            <div className="p-4 border border-gray-200 rounded-lg space-y-3 bg-gray-50 shadow">
              {searchConditions.map((condition: SearchCondition) => {
                 const canBeRemoved = searchConditions.length > 1 || (condition.type !== 'TEXT' || (condition.data as InternalTextSearchData).text.trim() !== '');
                 return (
                     <div key={condition.id} className="border border-gray-300 rounded-md bg-white shadow-sm flex items-stretch"> 
                        <div className="flex-grow min-w-0 border-r border-gray-300 flex items-center">{renderSearchConditionRow(condition, canBeRemoved)}</div>
                        <button onClick={() => { setIsSearchToolModalOpen(true); setEditingCondition(condition); }} className="p-2 text-gray-600 hover:bg-gray-100 rounded-r-md flex items-center justify-center focus:outline-none focus:ring-1 focus:ring-blue-500 flex-shrink-0" title={`Change tool type (current: ${condition.type})`} style={{ minWidth: '40px' }}>{getConditionTypeIcon(condition.type)}</button>
                     </div>
                 );
              })}
            </div>
          </div>
          <div className="pt-4 border-t border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-3">Search Fields</h3>
            <GooglePatentsFields fields={googleLikeFields} onFieldChange={onFieldChange} onPatentOfficeToggle={onPatentOfficeToggle} onLanguageToggle={onLanguageToggle} onAddDynamicEntry={onAddDynamicEntry} onRemoveDynamicEntry={onRemoveDynamicEntry} currentInventorInput={currentInventorInput} setCurrentInventorInput={setCurrentInventorInput} currentAssigneeInput={currentAssigneeInput} setCurrentAssigneeInput={setCurrentAssigneeInput} inventorInputRef={inventorInputRef} assigneeInputRef={assigneeInputRef} isPatentOfficeDropdownOpen={isPatentOfficeDropdownOpen} setIsPatentOfficeDropdownOpen={setIsPatentOfficeDropdownOpen} isLanguageDropdownOpen={isLanguageDropdownOpen} setIsLanguageDropdownOpen={setIsLanguageDropdownOpen} patentOfficeRef={patentOfficeRef} languageRef={languageRef} />
          </div>
        </>
      )}
      {isSearchToolModalOpen && editingCondition && ( <SearchToolModal isOpen={isSearchToolModalOpen} onClose={() => { setIsSearchToolModalOpen(false); setEditingCondition(undefined); }} onUpdateCondition={handleUpdateSearchConditionFromModal} initialCondition={editingCondition} /> )}
    </div>
  );
};

export default ChatInput;
// src/components/ChatInput.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { PatentFormat } from '../types';
import {
    XCircle, Type as TypeIcon, Wand2, Link as LinkIcon,
    AlertCircle
} from 'lucide-react';
import {
    SearchCondition, TextSearchCondition, PatentOffice, Language, 
    GoogleLikeSearchFields as GoogleLikeSearchFieldsType, DynamicEntry
} from './searchToolTypes';

import GooglePatentsFields from './googlePatents/GooglePatentsFields';
import { UsptoSpecificSettings } from './usptoPatents/usptoQueryBuilder';
import { generateQuery, parseQuery } from './googlePatents/googleApi';

const GOOGLE_OPERATORS = /\b(AND|OR|NOT|NEAR\d*|ADJ\d*)\b/gi;
const FIELDED_SYNTAX_HEURISTIC = /^\s*(inventor|assignee|cpc|ipc|pn|after|before|country|lang|status|type|is:litigated)[:=]/i;

function validateSearchTermText(text: string): string | null {
  const trimmedText = text.trim();
  if (!trimmedText) return null;

  // Don't validate if it looks like a fielded query, parser will handle it
  if (FIELDED_SYNTAX_HEURISTIC.test(trimmedText)) {
      return null;
  }

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

const ChatInput: React.FC<ChatInputProps> = ({
  value: mainQueryValue, activeFormat, onTabChange, onMainInputChange,
}) => {
  const createDefaultTextCondition = useCallback((): TextSearchCondition => ({
    id: crypto.randomUUID(), type: 'TEXT', data: { text: '', error: null }
  }), []);

  const [searchConditions, setSearchConditions] = useState<SearchCondition[]>([createDefaultTextCondition()]);
  const [googleLikeFields, setGoogleLikeFields] = useState<GoogleLikeSearchFieldsType>({
    dateFrom: '', dateTo: '', dateType: 'publication', inventors: [], assignees: [], patentOffices: [], languages: [], status: '', patentType: '', litigation: '',
  });
  const [usptoSpecificSettings, setUsptoSpecificSettings] = useState<UsptoSpecificSettings>({
    defaultOperator: 'AND', plurals: false, britishEquivalents: true, selectedDatabases: ['US-PGPUB', 'USPAT', 'USOCR'], highlights: 'SINGLE_COLOR', showErrors: true,
  });
  
  const [queryLinkHref, setQueryLinkHref] = useState<string>('#');
  const isInternalUpdate = useRef(false);
  
  const triggerQueryGeneration = useCallback(async () => {
    const hasErrors = searchConditions.some(c => c.data.error);
    if (hasErrors) {
      onMainInputChange('');
      setQueryLinkHref('#');
      return;
    }
    
    isInternalUpdate.current = true;
    const result = await generateQuery(activeFormat, searchConditions, googleLikeFields, usptoSpecificSettings);
    onMainInputChange(result.queryStringDisplay);
    setQueryLinkHref(result.url);
  }, [activeFormat, searchConditions, googleLikeFields, usptoSpecificSettings, onMainInputChange]);

  useEffect(() => {
    // This effect now correctly handles regeneration when any structured data changes.
    // The isInternalUpdate ref prevents an infinite loop from the main query input's onChange.
    if (isInternalUpdate.current) {
        isInternalUpdate.current = false;
        return;
    }
    triggerQueryGeneration();
  }, [googleLikeFields, searchConditions, usptoSpecificSettings, activeFormat, triggerQueryGeneration]);

  const manageSearchConditionInputs = (conditions: SearchCondition[]): SearchCondition[] => {
    let filteredConditions = conditions.filter((cond, index) => {
        if (cond.data.text.trim() === '') {
            const anotherEmptyExists = conditions.slice(index + 1).some(c => c.data.text.trim() === '');
            return !anotherEmptyExists;
        }
        return true;
    });
    const lastCondition = filteredConditions[filteredConditions.length - 1];
    const needsEmptyBox = !lastCondition || lastCondition.data.text.trim() !== '';
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
    onMainInputChange(e.target.value);
  };
  
  const handleMainQueryKeyDown = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        isInternalUpdate.current = true;
        try {
            const result = await parseQuery(activeFormat, mainQueryValue);
            
            const newSearchConditions = result.searchConditions.map(sc => ({
                ...sc,
                data: { ...sc.data, error: null }
            }));

            // FIX: Set state and let the useEffect handle regeneration. Do not call triggerQueryGeneration here.
            setSearchConditions(manageSearchConditionInputs(newSearchConditions));
            setGoogleLikeFields(result.googleLikeFields);
            setUsptoSpecificSettings(result.usptoSpecificSettings);

        } catch (error) {
            console.error("Parsing failed:", error);
            onMainInputChange(`Error parsing query: ${(error as Error).message}`);
        }
    }
  };

  const handleTabClick = (newFormat: PatentFormat) => onTabChange(newFormat);
  
  const onFieldChange = <K extends keyof GoogleLikeSearchFieldsType>(field: K, value: GoogleLikeSearchFieldsType[K]) => setGoogleLikeFields((prev: GoogleLikeSearchFieldsType) => ({ ...prev, [field]: value }));
  
  const updateSearchConditionText = (id: string, newText: string) => {
      setSearchConditions((prev: SearchCondition[]) => {
          const updated = prev.map(sc => {
              if (sc.id === id) {
                  const error = validateSearchTermText(newText);
                  return { ...sc, data: { ...sc.data, text: newText, error } };
              }
              return sc;
          });
          // FIX: Call manageSearchConditionInputs here to provide immediate UI feedback for adding new boxes.
          return manageSearchConditionInputs(updated);
      });
  };

  const removeSearchCondition = (id: string) => {
      setSearchConditions((prev: SearchCondition[]) => manageSearchConditionInputs(prev.filter(sc => sc.id !== id)));
  };

  const processIndividualTerm = async (id: string, text: string) => {
      // Trigger generation on blur/enter to reflect any non-fielded text changes
      triggerQueryGeneration();

      if (!FIELDED_SYNTAX_HEURISTIC.test(text)) {
          return; // Not a fielded query, nothing more to do
      }
      
      try {
          const result = await parseQuery(activeFormat, text);
          
          setGoogleLikeFields((prevFields: GoogleLikeSearchFieldsType) => {
              const newFields = { ...prevFields };
              newFields.inventors = [...prevFields.inventors, ...result.googleLikeFields.inventors];
              newFields.assignees = [...prevFields.assignees, ...result.googleLikeFields.assignees];
              newFields.patentOffices = [...prevFields.patentOffices, ...result.googleLikeFields.patentOffices];
              newFields.languages = [...prevFields.languages, ...result.googleLikeFields.languages];
              if (result.googleLikeFields.dateFrom) newFields.dateFrom = result.googleLikeFields.dateFrom;
              if (result.googleLikeFields.dateTo) newFields.dateTo = result.googleLikeFields.dateTo;
              if (result.googleLikeFields.dateType) newFields.dateType = result.googleLikeFields.dateType;
              if (result.googleLikeFields.status) newFields.status = result.googleLikeFields.status;
              if (result.googleLikeFields.patentType) newFields.patentType = result.googleLikeFields.patentType;
              if (result.googleLikeFields.litigation) newFields.litigation = result.googleLikeFields.litigation;
              return newFields;
          });

          const remainingText = result.searchConditions[0]?.data.text || '';
          setSearchConditions(prev => {
              const updated = prev.map(sc => 
                  sc.id === id ? { ...sc, data: { ...sc.data, text: remainingText, error: null } } : sc
              );
              return manageSearchConditionInputs(updated);
          });

      } catch (error) {
          console.error("Individual term parsing failed:", error);
          setSearchConditions(prev => prev.map(sc => sc.id === id ? {...sc, data: {...sc.data, error: "Invalid syntax"}} : sc));
      }
  };

  const renderSearchConditionRow = (condition: SearchCondition, canBeRemoved: boolean) => {
    const textData = condition.data;
    const hasError = !!textData.error;
    const isTextEmpty = textData.text.trim() === '';

    return (
      <div className={`flex items-center w-full ${hasError ? 'ring-2 ring-red-500 rounded-md' : ''}`}>
          <input 
            type="text" 
            value={textData.text} 
            onChange={(e) => updateSearchConditionText(condition.id, e.target.value)} 
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); processIndividualTerm(condition.id, textData.text); } }}
            onBlur={() => processIndividualTerm(condition.id, textData.text)}
            placeholder="Type a search term or a fielded query (e.g., inventor:doe)..." 
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
  };

  const [currentInventorInput, setCurrentInventorInput] = useState('');
  const [currentAssigneeInput, setCurrentAssigneeInput] = useState('');
  const inventorInputRef = useRef<HTMLInputElement>(null);
  const assigneeInputRef = useRef<HTMLInputElement>(null);
  const [isPatentOfficeDropdownOpen, setIsPatentOfficeDropdownOpen] = useState(false);
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
  const patentOfficeRef = useRef<HTMLDivElement>(null);
  const languageRef = useRef<HTMLDivElement>(null);
  const onPatentOfficeToggle = (office: PatentOffice) => setGoogleLikeFields((p: GoogleLikeSearchFieldsType) => ({...p, patentOffices: p.patentOffices.includes(office) ? p.patentOffices.filter(o => o !== office) : [...p.patentOffices, office]}));
  const onLanguageToggle = (lang: Language) => setGoogleLikeFields((p: GoogleLikeSearchFieldsType) => ({...p, languages: p.languages.includes(lang) ? p.languages.filter(l => l !== lang) : [...p.languages, lang]}));
  const onAddDynamicEntry = (field: 'inventors' | 'assignees') => {
    const value = field === 'inventors' ? currentInventorInput.trim() : currentAssigneeInput.trim();
    if (!value) return;
    const newEntry = { id: crypto.randomUUID(), value };
    setGoogleLikeFields((prev: GoogleLikeSearchFieldsType) => ({ ...prev, [field]: [...prev[field], newEntry] }));
    if (field === 'inventors') setCurrentInventorInput('');
    else setCurrentAssigneeInput('');
  };
  const onRemoveDynamicEntry = (field: 'inventors' | 'assignees', id: string) => {
    setGoogleLikeFields((prev: GoogleLikeSearchFieldsType) => ({ ...prev, [field]: prev[field].filter((entry: DynamicEntry) => entry.id !== id) }));
  };

  const formatTabs: Array<{ value: PatentFormat; label: string; icon: React.ReactNode }> = [
    { value: 'google', label: 'Google', icon: <TypeIcon size={18} /> },
    { value: 'uspto', label: 'USPTO', icon: <TypeIcon size={18} /> }
  ];

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
          <input id="main-query-input" type="text" value={mainQueryValue} onChange={handleMainQueryDirectInputChange} onKeyDown={handleMainQueryKeyDown} placeholder="Your generated query will appear here... or type a query and press Enter" className="w-full p-2 border-none focus:ring-0 text-sm bg-transparent outline-none" />
        </div>
      </div>
      {activeFormat === 'google' && (
        <>
          <div className="pt-4 border-t border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 flex items-center mb-3"> <Wand2 className="h-5 w-5 mr-2 text-blue-600" /> Search Terms </h3>
            <div className="p-4 border border-gray-200 rounded-lg space-y-3 bg-gray-50 shadow">
              {searchConditions.map((condition: SearchCondition) => {
                 const canBeRemoved = searchConditions.length > 1 || condition.data.text.trim() !== '';
                 return (
                     <div key={condition.id} className="border border-gray-300 rounded-md bg-white shadow-sm flex items-center"> 
                        {renderSearchConditionRow(condition, canBeRemoved)}
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
    </div>
  );
};

export default ChatInput;
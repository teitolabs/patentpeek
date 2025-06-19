// src/components/ChatInput.tsx
import React, { useState, useRef, useEffect } from 'react';
import { PatentFormat } from '../types';
import {
    XCircle, Type as TypeIcon, Wand2, Link as LinkIcon,
    AlertCircle
} from 'lucide-react';
import {
    SearchCondition, PatentOffice, Language, 
    GoogleLikeSearchFields as GoogleLikeSearchFieldsType, DynamicEntry
} from './searchToolTypes';

import GooglePatentsFields from './googlePatents/GooglePatentsFields';
import UsptoPatentsFields from './usptoPatents/UsptoPatentsFields';
import { parseQuery } from './googlePatents/googleApi';
import { useQueryBuilder } from './useQueryBuilder';
import ASTViewer from './ASTViewer';

const FIELDED_SYNTAX_HEURISTIC = /^\s*(inventor|assignee|cpc|ipc|pn|after|before|country|lang|status|type|is:litigated)[:=]/i;

export interface ChatInputProps {
  value: string;
  activeFormat: PatentFormat;
  onTabChange: (newFormat: PatentFormat) => void;
  onMainInputChange: (text: string) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({
  value: mainQueryValueFromProp, activeFormat, onTabChange, onMainInputChange,
}) => {
  const {
      mainQueryValue,
      queryLinkHref,
      ast,
      searchConditions,
      googleLikeFields,
      usptoSpecificSettings,
      onFieldChange,
      onUsptoFieldChange,
      setUsptoSpecificSettings, // This will now be used
      updateSearchConditionText,
      removeSearchCondition,
      handleParseAndApply,
      setGoogleLikeFields,
      setSearchConditions,
  } = useQueryBuilder(activeFormat);

  useEffect(() => {
    onMainInputChange(mainQueryValue);
  }, [mainQueryValue, onMainInputChange]);

  const handleMainQueryDirectInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onMainInputChange(e.target.value);
  };
  
  const handleMainQueryKeyDown = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        await handleParseAndApply(mainQueryValueFromProp);
    }
  };

  const handleTabClick = (newFormat: PatentFormat) => onTabChange(newFormat);
  
  const processIndividualTerm = async (id: string, text: string) => {
      if (!FIELDED_SYNTAX_HEURISTIC.test(text)) {
          return;
      }
      
      try {
          const result = await parseQuery(activeFormat, text);
          
          setGoogleLikeFields((prevFields: GoogleLikeSearchFieldsType) => {
              const newFields = { ...prevFields };
              newFields.inventors = [...new Set([...prevFields.inventors, ...result.googleLikeFields.inventors])];
              newFields.assignees = [...new Set([...prevFields.assignees, ...result.googleLikeFields.assignees])];
              newFields.patentOffices = [...new Set([...prevFields.patentOffices, ...result.googleLikeFields.patentOffices])];
              newFields.languages = [...new Set([...prevFields.languages, ...result.googleLikeFields.languages])];
              if (result.googleLikeFields.dateFrom) newFields.dateFrom = result.googleLikeFields.dateFrom;
              if (result.googleLikeFields.dateTo) newFields.dateTo = result.googleLikeFields.dateTo;
              if (result.googleLikeFields.dateType && result.googleLikeFields.dateType !== 'publication') newFields.dateType = result.googleLikeFields.dateType;
              if (result.googleLikeFields.status) newFields.status = result.googleLikeFields.status;
              if (result.googleLikeFields.patentType) newFields.patentType = result.googleLikeFields.patentType;
              if (result.googleLikeFields.litigation) newFields.litigation = result.googleLikeFields.litigation;
              return newFields;
          });

          const remainingText = result.searchConditions[0]?.data.text || '';
          updateSearchConditionText(id, remainingText);

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

  // --- START: FIX for the TypeScript errors ---
  // Create a dedicated handler for the databases checklist that correctly uses the state setter.
  const handleSelectedDatabasesChange: React.Dispatch<React.SetStateAction<string[]>> = (updater) => {
    setUsptoSpecificSettings(prevSettings => {
        const oldDatabases = prevSettings.selectedDatabases;
        const newDatabases = typeof updater === 'function' ? updater(oldDatabases) : updater;
        return { ...prevSettings, selectedDatabases: newDatabases };
    });
  };
  // --- END: FIX ---

  const [currentInventorInput, setCurrentInventorInput] = useState('');
  const [currentAssigneeInput, setCurrentAssigneeInput] = useState('');
  const inventorInputRef = useRef<HTMLInputElement>(null);
  const assigneeInputRef = useRef<HTMLInputElement>(null);
  const [isPatentOfficeDropdownOpen, setIsPatentOfficeDropdownOpen] = useState(false);
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
  const patentOfficeRef = useRef<HTMLDivElement>(null);
  const languageRef = useRef<HTMLDivElement>(null);
  
  const onPatentOfficeToggle = (office: PatentOffice) => onFieldChange('patentOffices', googleLikeFields.patentOffices.includes(office) ? googleLikeFields.patentOffices.filter(o => o !== office) : [...googleLikeFields.patentOffices, office]);
  const onLanguageToggle = (lang: Language) => onFieldChange('languages', googleLikeFields.languages.includes(lang) ? googleLikeFields.languages.filter(l => l !== lang) : [...googleLikeFields.languages, lang]);
  
  const onAddDynamicEntry = (field: 'inventors' | 'assignees') => {
    const value = field === 'inventors' ? currentInventorInput.trim() : currentAssigneeInput.trim();
    if (!value) return;
    const newEntry = { id: crypto.randomUUID(), value };
    onFieldChange(field, [...googleLikeFields[field], newEntry]);
    if (field === 'inventors') setCurrentInventorInput('');
    else setCurrentAssigneeInput('');
  };
  
  const onRemoveDynamicEntry = (field: 'inventors' | 'assignees', id: string) => {
    onFieldChange(field, googleLikeFields[field].filter((entry: DynamicEntry) => entry.id !== id));
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
          <input id="main-query-input" type="text" value={mainQueryValueFromProp} onChange={handleMainQueryDirectInputChange} onKeyDown={handleMainQueryKeyDown} placeholder="Your generated query will appear here... or type a query and press Enter" className="w-full p-2 border-none focus:ring-0 text-sm bg-transparent outline-none" />
        </div>
      </div>
      
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
        {activeFormat === 'google' && (
            <GooglePatentsFields fields={googleLikeFields} onFieldChange={onFieldChange} onPatentOfficeToggle={onPatentOfficeToggle} onLanguageToggle={onLanguageToggle} onAddDynamicEntry={onAddDynamicEntry} onRemoveDynamicEntry={onRemoveDynamicEntry} currentInventorInput={currentInventorInput} setCurrentInventorInput={setCurrentInventorInput} currentAssigneeInput={currentAssigneeInput} setCurrentAssigneeInput={setCurrentAssigneeInput} inventorInputRef={inventorInputRef} assigneeInputRef={assigneeInputRef} isPatentOfficeDropdownOpen={isPatentOfficeDropdownOpen} setIsPatentOfficeDropdownOpen={setIsPatentOfficeDropdownOpen} isLanguageDropdownOpen={isLanguageDropdownOpen} setIsLanguageDropdownOpen={setIsLanguageDropdownOpen} patentOfficeRef={patentOfficeRef} languageRef={languageRef} />
        )}
        {activeFormat === 'uspto' && (
            <UsptoPatentsFields 
                defaultOperator={usptoSpecificSettings.defaultOperator}
                setDefaultOperator={(val) => onUsptoFieldChange('defaultOperator', val)}
                highlights={usptoSpecificSettings.highlights}
                setHighlights={(val) => onUsptoFieldChange('highlights', val)}
                showErrors={usptoSpecificSettings.showErrors}
                setShowErrors={(val) => onUsptoFieldChange('showErrors', val)}
                plurals={usptoSpecificSettings.plurals}
                setPlurals={(val) => onUsptoFieldChange('plurals', val)}
                britishEquivalents={usptoSpecificSettings.britishEquivalents}
                setBritishEquivalents={(val) => onUsptoFieldChange('britishEquivalents', val)}
                selectedDatabases={usptoSpecificSettings.selectedDatabases}
                setSelectedDatabases={handleSelectedDatabasesChange} // <-- Use the new handler here
                onSearch={() => {}}
                onClear={() => {}}
                onPatentNumberSearch={() => {}}
            />
        )}
      </div>
      <ASTViewer ast={ast} />
    </div>
  );
};

export default ChatInput;
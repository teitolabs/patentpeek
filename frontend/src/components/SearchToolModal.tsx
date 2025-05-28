import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

// Import types from ChatInput.tsx (or a shared types.ts file)
import { 
    SearchCondition,      // The main union type for a condition
    SearchToolType, 
    InternalTextSearchData, // Specific data structure for TEXT tool
    ClassificationSearchData, // Specific data structure for CLASSIFICATION tool
    // Import other specific data structures as you define them (e.g., ChemistrySearchData)
    QueryScope,           // Used by Text tool
    TermOperator          // Used by Text tool
} from './ChatInput';     // Adjust path as necessary

// Union of all possible data structures the modal can send back to ChatInput
// This should align with the data parts of the SearchCondition union types
export type ModalToolData = InternalTextSearchData | ClassificationSearchData | { [key: string]: any }; // Add other tool data types

export interface SearchToolModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpdateCondition: (
    id: string,
    newType: SearchToolType, 
    newData: ModalToolData // This is what the modal sends back
  ) => void;
  initialCondition: SearchCondition; // Use the imported SearchCondition type
}

// --- Options for the "Text" tool ---
const scopeOptions: Array<{ value: QueryScope; label: string }> = [
  { value: 'FT', label: 'Full documents' }, { value: 'TI', label: 'Title' },
  { value: 'AB', label: 'Abstract' }, { value: 'CL', label: 'Claims' },
];
const operatorOptions: Array<{ value: TermOperator; label: string }> = [
  { value: 'ALL', label: 'All' }, { value: 'ANY', label: 'Any' },
  { value: 'EXACT', label: 'Exact' }, { value: 'NONE', label: 'Not' },
];
// --- Options for the "Classification" tool ---
const cpcOptions: Array<{ value: 'CHILDREN' | 'EXACT'; label: string}> = [
    { value: 'CHILDREN', label: 'These CPCs and their children'},
    { value: 'EXACT', label: 'These exact CPCs'},
];

const SearchToolModal: React.FC<SearchToolModalProps> = ({ 
  isOpen, 
  onClose, 
  onUpdateCondition, 
  initialCondition 
}) => {
  const [activeToolTab, setActiveToolTab] = useState<SearchToolType>(initialCondition.type);
  
  // State for "Text" tool
  const [textTool_text, setTextTool_Text] = useState('');
  const [textTool_selectedScopes, setTextTool_SelectedScopes] = useState<Set<QueryScope>>(new Set(['FT']));
  const [textTool_termOperator, setTextTool_TermOperator] = useState<TermOperator>('ALL');

  // State for "Classification" tool
  const [classificationTool_cpc, setClassificationTool_Cpc] = useState('');
  const [classificationTool_option, setClassificationTool_Option] = useState<'CHILDREN' | 'EXACT'>('CHILDREN');

  // TODO: Add state for Chemistry, Measure, Numbers tools

  useEffect(() => {
    if (isOpen) {
        setActiveToolTab(initialCondition.type); // Set active tab based on the condition being edited
        
        // Populate data based on the initial condition's type
        switch (initialCondition.type) {
            case 'TEXT':
                // initialCondition is SearchCondition, so initialCondition.data needs casting
                const textData = initialCondition.data as InternalTextSearchData;
                setTextTool_Text(textData.text || '');
                setTextTool_SelectedScopes(new Set(textData.selectedScopes || ['FT']));
                setTextTool_TermOperator(textData.termOperator || 'ALL');
                break;
            case 'CLASSIFICATION':
                const cpcData = initialCondition.data as ClassificationSearchData;
                setClassificationTool_Cpc(cpcData.cpc || '');
                setClassificationTool_Option(cpcData.option || 'CHILDREN');
                break;
            // TODO: Add cases for other tool types to populate their state
            default:
                // Reset all tool fields to default if type is new or unknown
                setTextTool_Text(''); setTextTool_SelectedScopes(new Set(['FT'])); setTextTool_TermOperator('ALL');
                setClassificationTool_Cpc(''); setClassificationTool_Option('CHILDREN');
                // TODO: Reset other tool states
                break;
        }
    }
  }, [isOpen, initialCondition]);

  const handleTabChange = (tab: SearchToolType) => {
    setActiveToolTab(tab);
    // When tab changes, populate fields if initialCondition matches the new tab,
    // otherwise reset fields for the new tab.
    if (initialCondition.type === tab) {
        switch (tab) {
            case 'TEXT':
                const textData = initialCondition.data as InternalTextSearchData;
                setTextTool_Text(textData.text || '');
                setTextTool_SelectedScopes(new Set(textData.selectedScopes || ['FT']));
                setTextTool_TermOperator(textData.termOperator || 'ALL');
                break;
            case 'CLASSIFICATION':
                const cpcData = initialCondition.data as ClassificationSearchData;
                setClassificationTool_Cpc(cpcData.cpc || '');
                setClassificationTool_Option(cpcData.option || 'CHILDREN');
                break;
            // TODO: Add cases for other tool types
        }
    } else { // Switched to a tab different from initial condition's type, reset its fields
        if (tab === 'TEXT') { setTextTool_Text(''); setTextTool_SelectedScopes(new Set(['FT'])); setTextTool_TermOperator('ALL'); }
        if (tab === 'CLASSIFICATION') { setClassificationTool_Cpc(''); setClassificationTool_Option('CHILDREN'); }
        // TODO: Reset other tool fields
    }
  };

  const handleTextToolToggleScope = (scope: QueryScope) => {
    const newScopes = new Set(textTool_selectedScopes);
    if (scope === 'FT') { newScopes.clear(); newScopes.add('FT'); }
    else {
      newScopes.delete('FT');
      if (newScopes.has(scope)) newScopes.delete(scope); else newScopes.add(scope);
      if (newScopes.size === 0) newScopes.add('FT');
    }
    setTextTool_SelectedScopes(newScopes);
  };

  const handleSubmitCondition = () => {
    let newData: ModalToolData;
    switch (activeToolTab) {
      case 'TEXT':
        if (!textTool_text.trim()) { alert("Please enter search text."); return; }
        newData = { 
          text: textTool_text.trim(), 
          selectedScopes: textTool_selectedScopes, 
          termOperator: textTool_termOperator 
        } as InternalTextSearchData; // Cast to specific type for clarity
        break;
      case 'CLASSIFICATION':
        if (!classificationTool_cpc.trim()) { alert("Please enter a CPC code."); return; }
        newData = { 
          cpc: classificationTool_cpc.trim(), 
          option: classificationTool_option 
        } as ClassificationSearchData; // Cast to specific type
        break;
      // TODO: Add cases for other tools, preparing their specific newData object
      default:
        alert(`Tool type "${activeToolTab}" is not yet fully implemented for submission.`);
        return; 
    }
    onUpdateCondition(initialCondition.id, activeToolTab, newData);
    onClose(); 
  };

  if (!isOpen) return null;

  // --- Render Functions for Each Tool ---
  const renderTextTool = (): React.ReactNode => (
    <div className="space-y-4">
      <input type="text" value={textTool_text} onChange={(e) => setTextTool_Text(e.target.value)} placeholder="Type a concept you want to search for here" className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"/>
      <div className="flex flex-wrap gap-2 items-center">
        {scopeOptions.map(opt => (<button key={opt.value} onClick={() => handleTextToolToggleScope(opt.value)} className={`px-3 py-1.5 text-sm font-medium rounded-md border ${textTool_selectedScopes.has(opt.value) ? 'bg-blue-500 text-white border-blue-500 ring-2 ring-blue-300' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}`}>{opt.label}</button>))}
      </div>
      <div className="flex flex-wrap gap-2 items-center">
        {operatorOptions.map(opt => (<button key={opt.value} onClick={() => setTextTool_TermOperator(opt.value)} className={`px-3 py-1.5 text-sm font-medium rounded-md border ${textTool_termOperator === opt.value ? 'bg-blue-500 text-white border-blue-500 ring-2 ring-blue-300' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}`}>{opt.label}</button>))}
      </div>
    </div>
  );

  const renderClassificationTool = (): React.ReactNode => (
    <div className="space-y-4">
        <input type="text" value={classificationTool_cpc} onChange={(e) => setClassificationTool_Cpc(e.target.value.toUpperCase())} placeholder="Enter a CPC here (e.g., H01L21/00)" className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"/>
        <div className="flex flex-wrap gap-2 items-center">
            {cpcOptions.map(opt => (<button key={opt.value} onClick={() => setClassificationTool_Option(opt.value)} className={`px-3 py-1.5 text-sm font-medium rounded-md border ${classificationTool_option === opt.value ? 'bg-blue-500 text-white border-blue-500 ring-2 ring-blue-300' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}`}>{opt.label}</button>))}
        </div>
    </div>
  );
  
  const renderChemistryTool = (): React.ReactNode => (<div className="text-gray-500 p-4 border border-dashed rounded-md">Chemistry Tool UI (TODO)</div>);
  const renderMeasureTool = (): React.ReactNode => (<div className="text-gray-500 p-4 border border-dashed rounded-md">Measure Tool UI (TODO)</div>);
  const renderNumbersTool = (): React.ReactNode => (<div className="text-gray-500 p-4 border border-dashed rounded-md">Numbers Tool UI (TODO)</div>);

  const renderContent = (): React.ReactNode => {
    switch (activeToolTab) {
      case 'TEXT': return renderTextTool();
      case 'CLASSIFICATION': return renderClassificationTool();
      case 'CHEMISTRY': return renderChemistryTool();
      case 'MEASURE': return renderMeasureTool();
      case 'NUMBERS': return renderNumbersTool();
      default: 
        // This case should ideally not be hit if activeToolTab is always a valid SearchToolType
        return <p>Error: Unknown tool type selected.</p>;
    }
  };
  
  const toolTabs: {label: string, type: SearchToolType}[] = [
    {label: 'Text', type: 'TEXT'}, {label: 'Classification', type: 'CLASSIFICATION'}, 
    {label: 'Chemistry', type: 'CHEMISTRY'}, {label: 'Measure', type: 'MEASURE'}, 
    {label: 'Numbers', type: 'NUMBERS'}
  ];

  // --- Main Modal Return JSX ---
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-2xl space-y-4" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">Search tools</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={24} /></button>
        </div>
        <div className="flex border-b border-gray-200 -mx-6 px-2"> {/* Adjusted for full-width border effect */}
          {toolTabs.map(tabInfo => (
            <button 
              key={tabInfo.type} 
              onClick={() => handleTabChange(tabInfo.type)} 
              className={`px-4 py-2 text-sm font-medium focus:outline-none ${activeToolTab === tabInfo.type ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700 hover:border-b-2 hover:border-gray-300'}`}
            >
              {tabInfo.label}
            </button>
          ))}
        </div>
        <div className="min-h-[200px] py-4">{renderContent()}</div> {/* Added padding to content area */}
        <button 
            onClick={handleSubmitCondition} 
            className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
        >
            {/* More robust check for "Update" vs "Add" might be needed if initialCondition.data can be empty for new items */}
            Update Condition 
            {/* Or: {initialCondition.id && initialCondition.data && Object.keys(initialCondition.data).length > 0 ? 'Update Condition' : 'Add AND condition'} */}
        </button>
      </div>
    </div>
  );
};

export default SearchToolModal;
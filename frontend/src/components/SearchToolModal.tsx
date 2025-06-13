// --- START OF FILE SearchToolModal.tsx ---
import React, { useState, useEffect } from 'react';
// FIX: Removed unused 'Columns' icon
import { X, HelpCircle, BarChart2, Settings, FlaskConical as FlaskConicalIcon, SlidersHorizontal, Globe2, AlignLeft, ListOrdered } from 'lucide-react';

// FIX: Changed the import path from './ChatInput' to the correct source './searchToolTypes'
import {
    SearchCondition,
    SearchToolType,
    InternalTextSearchData,
    ClassificationSearchData,
    ChemistrySearchData,
    MeasureSearchData,
    NumbersSearchData,
    ChemistryOperator,
    ChemistryUiOperatorLabel,
    ChemistryDocScope,
    QueryScope,
    TermOperator,
    DocumentNumberType
} from './searchToolTypes';

export type ModalToolData =
  | InternalTextSearchData
  | ClassificationSearchData
  | ChemistrySearchData
  | MeasureSearchData
  | NumbersSearchData
  | { [key: string]: any };

export interface SearchToolModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpdateCondition: (
    id: string,
    newType: SearchToolType,
    newData: ModalToolData
  ) => void;
  initialCondition: SearchCondition;
}

interface ToggleButtonProps {
  label: string;
  isActive: boolean;
  onClick: () => void;
  className?: string;
  icon?: React.ReactNode;
}
const ToggleButton: React.FC<ToggleButtonProps> = ({ label, isActive, onClick, className, icon }) => (
  <button
    type="button"
    onClick={onClick}
    className={`px-3 py-1.5 text-sm font-medium rounded-md border transition-colors flex items-center justify-center
                ${isActive
                  ? 'bg-blue-100 text-blue-700 border-blue-300 ring-1 ring-blue-400'
                  : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'}
                ${className}`}
  >
    {icon && <span className="mr-2">{icon}</span>}
    {label}
  </button>
);


const scopeOptions: Array<{ value: QueryScope; label: string }> = [
  { value: 'FT', label: 'Full documents' }, { value: 'TI', label: 'Title' },
  { value: 'AB', label: 'Abstract' }, { value: 'CL', label: 'Claims' },
];
const operatorOptions: Array<{ value: TermOperator; label: string }> = [
  { value: 'ALL', label: 'All' }, { value: 'ANY', label: 'Any' },
  { value: 'EXACT', label: 'Exact' }, { value: 'NONE', label: 'Not' },
];
const cpcOptions: Array<{ value: 'CHILDREN' | 'EXACT'; label: string}> = [
    { value: 'CHILDREN', label: 'These CPCs and their children'},
    { value: 'EXACT', label: 'These exact CPCs'},
];

// UI labels for Chemistry operators
const chemistryOperatorUiOptionsList: Array<{ backendValue: ChemistryOperator; uiLabel: ChemistryUiOperatorLabel }> = [
    { backendValue: 'EXACT', uiLabel: 'Exact' },
    { backendValue: 'EXACT', uiLabel: 'Exact Batch' },
    { backendValue: 'SIMILAR', uiLabel: 'Similar' },
    { backendValue: 'SUBSTRUCTURE', uiLabel: 'Substructure' },
    { backendValue: 'SMARTS', uiLabel: 'Substructure (SMARTS)' },
];
const chemistryDocScopeUiOptions: Array<{ value: ChemistryDocScope; label: string }> = [
    { value: 'FULL', label: 'Full documents' }, { value: 'CLAIMS_ONLY', label: 'Claims only' },
];

const documentNumberTypeOptions: Array<{ value: DocumentNumberType; label: string }> = [
    { value: 'APPLICATION', label: 'Application Numbers' },
    { value: 'PUBLICATION', label: 'Publication Numbers' },
    { value: 'EITHER', label: 'Either' },
];


const SearchToolModal: React.FC<SearchToolModalProps> = ({
  isOpen,
  onClose,
  onUpdateCondition,
  initialCondition
}) => {
  const [activeToolTab, setActiveToolTab] = useState<SearchToolType>(initialCondition.type);

  const [textTool_text, setTextTool_Text] = useState('');
  const [textTool_selectedScopes, setTextTool_SelectedScopes] = useState<Set<QueryScope>>(new Set(['FT']));
  const [textTool_termOperator, setTextTool_TermOperator] = useState<TermOperator>('ALL');

  const [classificationTool_cpc, setClassificationTool_Cpc] = useState('');
  const [classificationTool_option, setClassificationTool_Option] = useState<'CHILDREN' | 'EXACT'>('CHILDREN');

  const [chemistryTool_term, setChemistryTool_Term] = useState('');
  const [chemistryTool_uiOperatorLabel, setChemistryTool_UiOperatorLabel] = useState<ChemistryUiOperatorLabel>('Exact'); // Store UI label
  const [chemistryTool_docScope, setChemistryTool_DocScope] = useState<ChemistryDocScope>('FULL');

  const [measureTool_measurements, setMeasureTool_Measurements] = useState('');
  const [measureTool_unitsConcepts, setMeasureTool_UnitsConcepts] = useState('');

  const [numbersTool_docIdsText, setNumbersTool_DocIdsText] = useState('');
  const [numbersTool_numberType, setNumbersTool_NumberType] = useState<DocumentNumberType>('APPLICATION');
  const [numbersTool_countryRestriction, setNumbersTool_CountryRestriction] = useState('');
  const [numbersTool_preferredCountriesOrder, setNumbersTool_PreferredCountriesOrder] = useState('');


  useEffect(() => {
    if (isOpen) {
        setActiveToolTab(initialCondition.type);
        switch (initialCondition.type) {
            case 'TEXT':
                const textData = initialCondition.data;
                setTextTool_Text(textData.text || '');
                setTextTool_SelectedScopes(new Set(textData.selectedScopes || ['FT']));
                setTextTool_TermOperator(textData.termOperator || 'ALL');
                break;
            case 'CLASSIFICATION':
                const cpcData = initialCondition.data;
                setClassificationTool_Cpc(cpcData.cpc || '');
                setClassificationTool_Option(cpcData.option || 'CHILDREN');
                break;
            case 'CHEMISTRY':
                const chemData = initialCondition.data;
                setChemistryTool_Term(chemData.term || '');
                setChemistryTool_UiOperatorLabel(chemData.uiOperatorLabel || 'Exact');
                setChemistryTool_DocScope(chemData.docScope || 'FULL');
                break;
            case 'MEASURE':
                const measureData = initialCondition.data;
                setMeasureTool_Measurements(measureData.measurements || '');
                setMeasureTool_UnitsConcepts(measureData.units_concepts || '');
                break;
            case 'NUMBERS':
                const numData = initialCondition.data;
                setNumbersTool_DocIdsText(numData.doc_ids_text || '');
                setNumbersTool_NumberType(numData.number_type || 'APPLICATION');
                setNumbersTool_CountryRestriction(numData.country_restriction || '');
                setNumbersTool_PreferredCountriesOrder(numData.preferred_countries_order || '');
                break;
            default:
                const _exhaustiveCheck: never = initialCondition;
                console.warn("Initial condition has unhandled type:", _exhaustiveCheck)
                setTextTool_Text(''); setTextTool_SelectedScopes(new Set(['FT'])); setTextTool_TermOperator('ALL');
                setClassificationTool_Cpc(''); setClassificationTool_Option('CHILDREN');
                setChemistryTool_Term(''); setChemistryTool_UiOperatorLabel('Exact'); setChemistryTool_DocScope('FULL');
                setMeasureTool_Measurements(''); setMeasureTool_UnitsConcepts('');
                setNumbersTool_DocIdsText(''); setNumbersTool_NumberType('APPLICATION'); setNumbersTool_CountryRestriction(''); setNumbersTool_PreferredCountriesOrder('');
                break;
        }
    }
  }, [isOpen, initialCondition]);

  const handleTabChange = (tab: SearchToolType) => {
    setActiveToolTab(tab);
    // If switching to a tab that's different from the initial condition's type, reset its fields.
    // If switching back to the initial condition's type, useEffect will handle repopulation.
    if (initialCondition.type !== tab) {
        if (tab === 'TEXT') { setTextTool_Text(''); setTextTool_SelectedScopes(new Set(['FT'])); setTextTool_TermOperator('ALL'); }
        else if (tab === 'CLASSIFICATION') { setClassificationTool_Cpc(''); setClassificationTool_Option('CHILDREN'); }
        else if (tab === 'CHEMISTRY') { setChemistryTool_Term(''); setChemistryTool_UiOperatorLabel('Exact'); setChemistryTool_DocScope('FULL'); }
        else if (tab === 'MEASURE') { setMeasureTool_Measurements(''); setMeasureTool_UnitsConcepts('');}
        else if (tab === 'NUMBERS') { setNumbersTool_DocIdsText(''); setNumbersTool_NumberType('APPLICATION'); setNumbersTool_CountryRestriction(''); setNumbersTool_PreferredCountriesOrder('');}
        else {
            const _exhaustiveCheckTabTypeMismatch: never = tab;
            console.warn("Unhandled tab type in handleTabChange (initialCondition.type !== tab):", _exhaustiveCheckTabTypeMismatch);
        }
    } else {
      // If it's the same tab as initialCondition.type, ensure state is correctly set from initialCondition
      // This is mainly handled by useEffect, but for complex cases, explicit reset might be needed.
      // For Chemistry, ensure uiOperatorLabel is correctly set from initialCondition.data.uiOperatorLabel
      if (tab === 'CHEMISTRY' && initialCondition.type === 'CHEMISTRY') {
        setChemistryTool_UiOperatorLabel(initialCondition.data.uiOperatorLabel || 'Exact');
      }
    }
  };

  const handleTextToolToggleScope = (scope: QueryScope) => { /* ... */ 
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
        } as InternalTextSearchData;
        break;
      case 'CLASSIFICATION':
        if (!classificationTool_cpc.trim()) { alert("Please enter a CPC code."); return; }
        newData = {
          cpc: classificationTool_cpc.trim(),
          option: classificationTool_option
        } as ClassificationSearchData;
        break;
      case 'CHEMISTRY':
        if (!chemistryTool_term.trim()) { alert("Please enter a chemical term, SMILES, etc."); return; }
        const selectedChemOp = chemistryOperatorUiOptionsList.find(opt => opt.uiLabel === chemistryTool_uiOperatorLabel);
        newData = {
            term: chemistryTool_term.trim(),
            operator: selectedChemOp ? selectedChemOp.backendValue : 'EXACT', // Map UI label to backend operator
            uiOperatorLabel: chemistryTool_uiOperatorLabel, // Store the UI label for state restoration
            docScope: chemistryTool_docScope
        } as ChemistrySearchData;
        break;
      case 'MEASURE':
        if (!measureTool_measurements.trim() && !measureTool_unitsConcepts.trim()) {
             alert("Please enter measurements or units/concepts."); return;
        }
        newData = { 
            measurements: measureTool_measurements.trim(),
            units_concepts: measureTool_unitsConcepts.trim()
        } as MeasureSearchData;
        break;
      case 'NUMBERS':
        if (!numbersTool_docIdsText.trim()) { alert("Please enter at least one document ID."); return; }
        newData = { 
            doc_ids_text: numbersTool_docIdsText.trim(),
            number_type: numbersTool_numberType,
            country_restriction: numbersTool_countryRestriction.trim().toUpperCase(),
            preferred_countries_order: numbersTool_preferredCountriesOrder.trim().toUpperCase()
        } as NumbersSearchData;
        break;
      default:
        const _exhaustiveCheck: never = activeToolTab;
        alert(`Tool type "${_exhaustiveCheck}" is not yet fully implemented for submission.`);
        return;
    }
    onUpdateCondition(initialCondition.id, activeToolTab, newData);
    onClose();
  };

  if (!isOpen) return null;

  const renderTextTool = (): React.ReactNode => ( <div className="space-y-4">
      <input type="text" value={textTool_text} onChange={(e) => setTextTool_Text(e.target.value)} placeholder="Type a concept you want to search for here" className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"/>
      <div className="flex flex-wrap gap-2 items-center">
        {scopeOptions.map(opt => (<ToggleButton key={opt.value} label={opt.label} isActive={textTool_selectedScopes.has(opt.value)} onClick={() => handleTextToolToggleScope(opt.value)} />))}
      </div>
      <div className="flex flex-wrap gap-2 items-center">
        {operatorOptions.map(opt => (<ToggleButton key={opt.value} label={opt.label} isActive={textTool_termOperator === opt.value} onClick={() => setTextTool_TermOperator(opt.value)} />))}
      </div>
    </div>);

  const renderClassificationTool = (): React.ReactNode => ( <div className="space-y-4">
        <input type="text" value={classificationTool_cpc} onChange={(e) => setClassificationTool_Cpc(e.target.value.toUpperCase())} placeholder="Enter a CPC here (e.g., H01L21/00)" className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"/>
        <div className="flex flex-wrap gap-2 items-center">
            {cpcOptions.map(opt => (<ToggleButton key={opt.value} label={opt.label} isActive={classificationTool_option === opt.value} onClick={() => setClassificationTool_Option(opt.value)} />))}
        </div>
    </div>);

  const renderChemistryTool = (): React.ReactNode => (
    <div className="space-y-6">
        <div className="relative">
            <AlignLeft className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input 
                type="text" 
                value={chemistryTool_term} 
                onChange={(e) => setChemistryTool_Term(e.target.value)} 
                placeholder="Trade name, SMILES, InChI Key" 
                className="w-full p-3 pl-10 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
            <span title="Enter chemical identifiers like name, SMILES, InChI, InChIKey, or CAS Registry Number.">
                <HelpCircle className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 cursor-pointer"/>
            </span>
        </div>
        <div className="flex items-center space-x-3">
            <FlaskConicalIcon className="h-5 w-5 text-gray-500 flex-shrink-0" />
            <div className="flex flex-wrap gap-2">
                {chemistryOperatorUiOptionsList.map(opt => (
                    <ToggleButton 
                        key={opt.uiLabel}
                        label={opt.uiLabel} 
                        isActive={chemistryTool_uiOperatorLabel === opt.uiLabel} 
                        onClick={() => setChemistryTool_UiOperatorLabel(opt.uiLabel)}
                    />
                ))}
            </div>
        </div>
        <div className="flex items-center space-x-3">
            <Settings className="h-5 w-5 text-gray-500 flex-shrink-0" />
            <div className="flex flex-wrap gap-2">
                {chemistryDocScopeUiOptions.map(opt => (
                    <ToggleButton 
                        key={opt.value} 
                        label={opt.label} 
                        isActive={chemistryTool_docScope === opt.value} 
                        onClick={() => setChemistryTool_DocScope(opt.value)} 
                    />
                ))}
            </div>
        </div>
    </div>
  );

  const renderMeasureTool = (): React.ReactNode => ( /* ... */ <div className="space-y-6">
        <div>
            <div className="relative">
                <AlignLeft className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input 
                    type="text" 
                    value={measureTool_measurements} 
                    onChange={(e) => setMeasureTool_Measurements(e.target.value)} 
                    placeholder="1.5 mm, 20 ft, 400-500 fahrenheit, 800 MHz, 0.01-100 mol" 
                    className="w-full p-3 pl-10 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
            </div>
        </div>
        <div>
            <div className="relative">
                <BarChart2 className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input 
                    type="text" 
                    value={measureTool_unitsConcepts} 
                    onChange={(e) => setMeasureTool_UnitsConcepts(e.target.value)} 
                    placeholder="activity, wavelength, embossing depth, absorption" 
                    className="w-full p-3 pl-10 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
            </div>
        </div>
    </div>);

  const renderNumbersTool = (): React.ReactNode => (
    <div className="space-y-6">
        <div className="relative">
            <AlignLeft className="absolute left-3 top-4 h-5 w-5 text-gray-400" />
            <textarea
                value={numbersTool_docIdsText}
                onChange={(e) => setNumbersTool_DocIdsText(e.target.value.toUpperCase())}
                placeholder="Enter multiple Patent Application and Publication Numbers, one per line"
                className="w-full p-3 pl-10 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 min-h-[80px] resize-y" // Adjusted height
                rows={3}
            />
        </div>
        <div className="flex items-center space-x-3">
            <SlidersHorizontal className="h-5 w-5 text-gray-500 flex-shrink-0" />
            <div className="flex flex-wrap gap-2">
                {documentNumberTypeOptions.map(opt => (
                    <ToggleButton
                        key={opt.value}
                        label={opt.label}
                        isActive={numbersTool_numberType === opt.value}
                        onClick={() => setNumbersTool_NumberType(opt.value)}
                    />
                ))}
            </div>
        </div>
        <div>
            <div className="relative">
                 <Globe2 className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                    type="text"
                    value={numbersTool_countryRestriction}
                    onChange={(e) => setNumbersTool_CountryRestriction(e.target.value.toUpperCase())}
                    placeholder="Restrict search to these countries (e.g. US, EP, WO)"
                    className="w-full p-3 pl-10 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
            </div>
        </div>
        <div>
            <div className="relative">
                 <ListOrdered className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                    type="text"
                    value={numbersTool_preferredCountriesOrder}
                    onChange={(e) => setNumbersTool_PreferredCountriesOrder(e.target.value.toUpperCase())}
                    placeholder="Prefer results from these countries in this order (e.g. US, EP)"
                    className="w-full p-3 pl-10 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
            </div>
        </div>
    </div>
  );

  const renderContent = (): React.ReactNode => { /* ... */ 
    switch (activeToolTab) {
      case 'TEXT': return renderTextTool();
      case 'CLASSIFICATION': return renderClassificationTool();
      case 'CHEMISTRY': return renderChemistryTool();
      case 'MEASURE': return renderMeasureTool();
      case 'NUMBERS': return renderNumbersTool();
      default:
        const _exhaustiveCheck: never = activeToolTab;
        return <p>Error: Unknown tool type selected: {_exhaustiveCheck}</p>;
    }
  };

  const toolTabs: {label: string, type: SearchToolType}[] = [
    {label: 'Text', type: 'TEXT'}, {label: 'Classification', type: 'CLASSIFICATION'},
    {label: 'Chemistry', type: 'CHEMISTRY'}, {label: 'Measure', type: 'MEASURE'},
    {label: 'Numbers', type: 'NUMBERS'}
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-2xl space-y-4" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">Search tools</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={24} /></button>
        </div>
        <div className="flex border-b border-gray-200 -mx-6 px-2 overflow-x-auto">
          {toolTabs.map(tabInfo => (
            <button
              key={tabInfo.type}
              onClick={() => handleTabChange(tabInfo.type)}
              className={`px-4 py-2 text-sm font-medium focus:outline-none whitespace-nowrap ${activeToolTab === tabInfo.type ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700 hover:border-b-2 hover:border-gray-300'}`}
            >
              {tabInfo.label}
            </button>
          ))}
        </div>
        <div className="min-h-[250px] py-4">{renderContent()}</div> {/* Slightly increased min-height for Numbers tool */}
        <button
            onClick={handleSubmitCondition}
            className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
        >
            Update Condition
        </button>
      </div>
    </div>
  );
};

export default SearchToolModal;
// --- END OF FILE SearchToolModal.tsx ---
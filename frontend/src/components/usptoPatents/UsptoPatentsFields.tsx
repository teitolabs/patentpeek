// src/components/usptoPatents/UsptoPatentsFields.tsx
import React from 'react';

export interface UsptoPatentsFieldsProps {
  defaultOperator: string;
  setDefaultOperator: (value: string) => void;
  highlights: string;
  setHighlights: (value: string) => void;
  showErrors: boolean;
  setShowErrors: (value: boolean) => void;
  plurals: boolean;
  setPlurals: (value: boolean) => void;
  britishEquivalents: boolean;
  setBritishEquivalents: (value: boolean) => void;
  selectedDatabases: string[];
  setSelectedDatabases: React.Dispatch<React.SetStateAction<string[]>>;
  onSearch: () => void;
  onClear: () => void;
  onPatentNumberSearch: () => void;
}

const USPTO_DATABASES = [
  { id: 'US-PGPUB', label: 'US-PGPUB (US Pre-Grant Publications)' },
  { id: 'USPAT', label: 'USPAT (US Patents Full Text)' },
  { id: 'USOCR', label: 'USOCR (US Optical Character Recognition)' },
];

const defaultOperatorOptions = ['AND', 'OR', 'ADJ', 'NEAR', 'SAME', 'WITH'];
const highlightOptions = [
    { value: 'NONE', label: 'None' },
    { value: 'SINGLE_COLOR', label: 'Single Color' },
    { value: 'MULTI_COLOR', label: 'Multi-color' },
];


const UsptoPatentsFields: React.FC<UsptoPatentsFieldsProps> = ({
  defaultOperator, setDefaultOperator,
  highlights, setHighlights,
  showErrors, setShowErrors,
  plurals, setPlurals,
  britishEquivalents, setBritishEquivalents,
  selectedDatabases, setSelectedDatabases,
  onSearch, onClear, onPatentNumberSearch
}) => {

  const handleDatabaseChange = (dbId: string) => {
    setSelectedDatabases((prevSelected: string[]) =>
      prevSelected.includes(dbId) 
        ? prevSelected.filter((id: string) => id !== dbId)
        : [...prevSelected, dbId]
    );
  };

  const handleSelectAllDatabases = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedDatabases(USPTO_DATABASES.map(db => db.id));
    } else {
      setSelectedDatabases([]);
    }
  };

  const isAllDatabasesSelected = selectedDatabases.length === USPTO_DATABASES.length;

  return (
    <div className="flex flex-col md:flex-row gap-4 p-1 text-sm">
      {/* Main Options Area */}
      <div className="flex-grow space-y-4 p-4 border border-gray-300 rounded-md bg-gray-50 shadow-sm">
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-end">
          <div>
            <label htmlFor="usptoDefaultOperator" className="block text-xs font-medium text-gray-700 mb-1">
              Default Operator:
            </label>
            <select
              id="usptoDefaultOperator"
              value={defaultOperator}
              onChange={(e) => setDefaultOperator(e.target.value)}
              className="block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              {defaultOperatorOptions.map(op => <option key={op} value={op}>{op}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="usptoHighlights" className="block text-xs font-medium text-gray-700 mb-1">
              Highlights:
            </label>
            <select
              id="usptoHighlights"
              value={highlights}
              onChange={(e) => setHighlights(e.target.value)}
              className="block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              {highlightOptions.map(op => <option key={op.value} value={op.value}>{op.label}</option>)}
            </select>
          </div>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-2 items-center">
          <div className="flex items-center">
            <input
              id="usptoShowErrors"
              type="checkbox"
              checked={showErrors}
              onChange={(e) => setShowErrors(e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="usptoShowErrors" className="ml-2 text-gray-700">
              Show Errors
            </label>
          </div>
          <div className="flex items-center">
            <input
              id="usptoPlurals"
              type="checkbox"
              checked={plurals}
              onChange={(e) => setPlurals(e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="usptoPlurals" className="ml-2 text-gray-700">
              Plurals
            </label>
          </div>
          <div className="flex items-center">
            <input
              id="usptoBritishEquivalents"
              type="checkbox"
              checked={britishEquivalents}
              onChange={(e) => setBritishEquivalents(e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="usptoBritishEquivalents" className="ml-2 text-gray-700">
              British Equivalents
            </label>
          </div>
        </div>

        <div className="flex gap-2 mt-4 pt-4 border-t border-gray-200 justify-end">
          <button
            type="button"
            onClick={onClear}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Clear
          </button>
          <button
            type="button"
            onClick={onPatentNumberSearch}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            PN
          </button>
          <button
            type="button"
            onClick={onSearch}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Search
          </button>
        </div>
      </div>

      {/* Databases Sidebar Area */}
      <div className="w-full md:w-64 flex-shrink-0 p-4 border border-gray-300 rounded-md bg-gray-50 shadow-sm">
        <h4 className="font-medium text-gray-900 mb-2">Databases</h4>
        <div className="space-y-2">
          <div className="flex items-center">
            <input
              id="usptoSelectAllDb"
              type="checkbox"
              checked={isAllDatabasesSelected}
              onChange={handleSelectAllDatabases}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="usptoSelectAllDb" className="ml-2 text-gray-700 font-medium">
              Select all
            </label>
          </div>
          <hr className="my-1"/>
          {USPTO_DATABASES.map(db => (
            <div key={db.id} className="flex items-center">
              <input
                id={`usptoDb-${db.id}`}
                type="checkbox"
                checked={selectedDatabases.includes(db.id)}
                onChange={() => handleDatabaseChange(db.id)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor={`usptoDb-${db.id}`} className="ml-2 text-gray-700 truncate" title={db.label}>
                {db.id}
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UsptoPatentsFields;
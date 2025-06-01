// src/components/ChatContainer.tsx
import React, { useState, useEffect } from 'react';
import ChatInput from './ChatInput';
import { PatentFormat } from '../types';
// Removed: import { convertQuery } from '../utils/converter'; // No longer used here

const ChatContainer: React.FC<{ key: number }> = ({ key: resetKeyProp }) => {
  const [currentText, setCurrentText] = useState('');
  const [activeFormat, setActiveFormat] = useState<PatentFormat>('google');
  // USPTO settings from query_converter.py, if any (e.g. parsed SET commands)
  // This state is not directly used by ChatInput's USPTOFields, but could be if needed
  const [_usptoSettingsFromConversion, setUsptoSettingsFromConversion] = useState<any>(null);


  useEffect(() => {
    setCurrentText('');
    setActiveFormat('google');
    setUsptoSettingsFromConversion(null);
  }, [resetKeyProp]);

  const handleMainInputChange = (text: string) => {
    setCurrentText(text);
  };

  const handleTabChange = async (newActiveFormat: PatentFormat) => {
    if (newActiveFormat === activeFormat) return;

    const previousActiveFormat = activeFormat;
    const textToConvert = currentText; // Use the current main query text

    if (textToConvert.trim() && previousActiveFormat !== 'unknown' && newActiveFormat !== 'unknown') {
      try {
        const response = await fetch('/api/convert-query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query_string: textToConvert,
            source_format: previousActiveFormat,
            target_format: newActiveFormat,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: `HTTP error! status: ${response.status}` }));
          console.error("Conversion API Error:", errorData);
          setCurrentText(`Error converting: ${errorData.error || response.statusText}`);
          // Fallback: still switch format, but with error message or original text
        } else {
          const result = await response.json();
          if (result.error) {
            console.error("Conversion Error from backend:", result.error);
            setCurrentText(`Error: ${result.error}`);
          } else if (result.converted_text !== null && result.converted_text !== undefined) {
            setCurrentText(result.converted_text);
            if (newActiveFormat === 'uspto' && result.settings) {
              setUsptoSettingsFromConversion(result.settings);
              // Potentially update ChatInput's usptoSettings state here if needed
              // For example: if result.settings.defaultoperator exists, update usptoDefaultOperator
            }
          } else {
             // Conversion resulted in empty or null, but no explicit error
            setCurrentText("");
          }
        }
      } catch (error) {
        console.error("Failed to call conversion API:", error);
        setCurrentText(error instanceof Error ? `API Error: ${error.message}` : "Network error during conversion");
      }
    } else if (!textToConvert.trim()) {
        // If current text is empty, just switch format and clear text
        setCurrentText("");
    }
    // Always update the active format
    setActiveFormat(newActiveFormat);
  };
  

  return (
    <div className="bg-white flex flex-col"> 
      <div className="p-4 md:px-6 md:pt-6 md:pb-2">
        <ChatInput
          value={currentText}
          activeFormat={activeFormat}
          onTabChange={handleTabChange}
          onMainInputChange={handleMainInputChange}
        />
      </div>
      {/* ChatMessages component removed as per instructions in thought process */}
    </div>
  );
};

export default ChatContainer;
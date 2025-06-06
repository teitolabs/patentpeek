// src/components/ChatContainer.tsx
import React, { useState, useEffect } from 'react';
import ChatInput from './ChatInput';
import { PatentFormat } from '../types';
import { convertQuery } from './googlePatents/googleApi'; // Use the new API client

const ChatContainer: React.FC<{ key: number }> = ({ key: resetKeyProp }) => {
  const [currentText, setCurrentText] = useState('');
  const [activeFormat, setActiveFormat] = useState<PatentFormat>('google');

  useEffect(() => {
    setCurrentText('');
    setActiveFormat('google');
  }, [resetKeyProp]);

  const handleMainInputChange = (text: string) => {
    setCurrentText(text);
  };

  const handleTabChange = async (newActiveFormat: PatentFormat) => {
    if (newActiveFormat === activeFormat) return;

    const previousActiveFormat = activeFormat;
    const textToConvert = currentText;

    setActiveFormat(newActiveFormat); // Switch format immediately for better UX

    if (textToConvert.trim() && !textToConvert.startsWith("Error") && !textToConvert.startsWith("API Error")) {
      try {
        const result = await convertQuery(textToConvert, previousActiveFormat, newActiveFormat);
        if (result.error) {
          setCurrentText(`Error converting: ${result.error}`);
        } else if (result.converted_text !== null) {
          setCurrentText(result.converted_text);
        } else {
          setCurrentText(""); // Handle case where conversion results in empty
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
        setCurrentText(`Error: ${errorMessage}`);
      }
    } else {
      // If the current text is empty or an error, just clear it on tab switch
      setCurrentText("");
    }
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
    </div>
  );
};

export default ChatContainer;
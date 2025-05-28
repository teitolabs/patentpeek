import React, { useState, useEffect } from 'react';
import ChatInput from './ChatInput';
import { /*Message,*/ PatentFormat } from '../types'; // Message might not be needed if no messages are stored/displayed
import { convertQuery } from '../utils/converter';
// import ChatMessages from './ChatMessages'; // REMOVE THIS IMPORT

const ChatContainer: React.FC<{ key: number }> = ({ key: resetKeyProp }) => {
  // const [messages, setMessages] = useState<Message[]>([]); // REMOVE if not storing/displaying messages
  const [currentText, setCurrentText] = useState(''); // This is the main query value
  const [activeFormat, setActiveFormat] = useState<PatentFormat>('google');

  useEffect(() => {
    // setMessages([]); // REMOVE
    setCurrentText('');
    setActiveFormat('google');
  }, [resetKeyProp]);

  const updateCurrentState = (text: string, format: PatentFormat) => {
    setCurrentText(text);
    setActiveFormat(format);
  };

  const handleMainInputChange = (text: string) => {
    setCurrentText(text);
  };

  const handleTabChange = (newActiveFormat: PatentFormat) => {
    if (newActiveFormat === activeFormat) return;

    const previousActiveFormat = activeFormat;

    if (currentText.trim() && previousActiveFormat !== newActiveFormat && previousActiveFormat !== 'unknown') {
      const result = convertQuery(currentText, previousActiveFormat, newActiveFormat);
      
      // If you still want to log conversions or handle them internally, keep this logic.
      // Otherwise, if messages are completely gone, this part might be simplified or removed too.
      // For now, we'll assume the conversion should still happen for the currentText.
      // const infoMessage: Message = { /* ... */ };
      // const originalQueryMessage: Message = { /* ... */ };
      // const convertedQueryMessage: Message = { /* ... */ };
      // setMessages(prev => [...prev, infoMessage, originalQueryMessage, convertedQueryMessage]); // REMOVE

      updateCurrentState(result.text, result.format);
    } else {
      updateCurrentState(currentText, newActiveFormat); 
    }
  };

  return (
    // Adjusted height calculation if ChatMessages is gone and ChatInput is the main content
    <div className="bg-white flex flex-col"> 
      <div className="p-4 md:px-6 md:pt-6 md:pb-2">
        <ChatInput
          value={currentText}
          activeFormat={activeFormat}
          onTabChange={handleTabChange}
          onMainInputChange={handleMainInputChange}
        />
      </div>
      {/* <ChatMessages messages={messages} /> REMOVE THIS COMPONENT */}
    </div>
  );
};

export default ChatContainer;
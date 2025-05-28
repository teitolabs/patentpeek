import React, { useState } from 'react';
import { Copy, CheckCircle, Notebook as Robot, User } from 'lucide-react';
import { Message, PatentFormat } from '../types';

interface ChatMessageProps {
  message: Message;
}

const getFormatLabel = (format: PatentFormat | undefined): string => { // Allow undefined for safety
  switch (format) {
    case 'google': return 'Google Patents';
    case 'uspto': return 'USPTO';
    case 'unknown': return 'Unknown Format';
    default: return 'Format'; // Fallback for undefined or unexpected
  }
};

const getFormatColor = (format: PatentFormat | undefined): string => { // Allow undefined for safety
  switch (format) {
    case 'google': return 'bg-blue-100 text-blue-800';
    case 'uspto': return 'bg-emerald-100 text-emerald-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.sender === 'user';
  
  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Determine the original format label for "Converted from" text
  let originalFormatLabel = '';
  if (message.originalText && message.originalFormat) {
     originalFormatLabel = getFormatLabel(message.originalFormat);
  } else if (message.originalText) {
    // Fallback logic if originalFormat is not explicitly provided
    // This assumes a direct toggle between google and uspto if originalFormat is missing
    if (message.format === 'google') originalFormatLabel = getFormatLabel('uspto');
    else if (message.format === 'uspto') originalFormatLabel = getFormatLabel('google');
  }


  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex items-start max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          {isUser ? (
            <User className="h-8 w-8 rounded-full bg-blue-100 p-1 text-blue-600" />
          ) : (
            <Robot className="h-8 w-8 rounded-full bg-gray-100 p-1 text-gray-600" />
          )}
        </div>
        
        <div className={`rounded-lg px-4 py-3 shadow-sm ${
          isUser 
            ? 'bg-blue-600 text-white' 
            : 'bg-white border border-gray-200'
        }`}>
          {message.format && !isUser && (
            <div className="flex items-center mb-2">
              <span className={`text-xs font-medium px-2 py-1 rounded-full ${getFormatColor(message.format)}`}>
                {getFormatLabel(message.format)}
              </span>
              {message.originalText && originalFormatLabel && (
                <span className="text-xs ml-2 text-gray-500">
                  Converted from {originalFormatLabel}
                </span>
              )}
            </div>
          )}
          
          <p className={`text-sm whitespace-pre-wrap ${isUser ? 'text-white' : 'text-gray-800'}`}>
            {message.text}
          </p>
          
          {!isUser && (
            <button 
              onClick={copyToClipboard}
              className="mt-2 inline-flex items-center text-xs text-gray-500 hover:text-gray-700 transition-colors"
            >
              {copied ? (
                <>
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
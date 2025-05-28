import React from 'react';
import { BookOpenText } from 'lucide-react';

interface ChatHeaderProps {
  onReset: () => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({ onReset }) => {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-700 text-white border-b border-blue-800">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <button
          onClick={onReset}
          className="flex items-center hover:opacity-80 transition-opacity"
        >
          <BookOpenText className="h-8 w-8 text-blue-100" />
          <h1 className="ml-2 text-xl font-semibold">PatentPeek</h1>
        </button>
      </div>
    </header>
  );
};

export default ChatHeader;
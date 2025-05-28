// src/App.tsx
import { useState } from 'react';
import ChatHeader from './components/ChatHeader';
import ChatContainer from './components/ChatContainer';
// import SyntaxExplanation from './components/SyntaxExplanation'; // REMOVE THIS LINE

function App() {
  const [key, setKey] = useState(0);

  const handleReset = () => {
    setKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-white">
      <ChatHeader onReset={handleReset} />
      <main className="container mx-auto max-w-3xl px-4 py-8 md:py-12">
        <ChatContainer key={key} />
        {/* <SyntaxExplanation /> REMOVE THIS LINE */}
      </main>
    </div>
  );
}

export default App;
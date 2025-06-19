// src/components/ASTViewer.tsx
import React from 'react';
import { Code2 } from 'lucide-react';

interface ASTViewerProps {
  ast: Record<string, any> | null;
}

const ASTViewer: React.FC<ASTViewerProps> = ({ ast }) => {
  if (!ast) {
    return null; // Don't render anything if there's no AST
  }

  return (
    <div className="pt-4 border-t border-gray-200">
      <details className="group">
        <summary className="flex items-center gap-2 text-lg font-medium text-gray-700 cursor-pointer">
          <Code2 className="h-5 w-5 text-purple-600" />
          <span>Live Abstract Syntax Tree (AST)</span>
        </summary>
        <div className="mt-2 bg-gray-800 text-white rounded-lg p-4">
          <pre className="text-xs whitespace-pre-wrap">
            <code>
              {JSON.stringify(ast, null, 2)}
            </code>
          </pre>
        </div>
      </details>
    </div>
  );
};

export default ASTViewer;
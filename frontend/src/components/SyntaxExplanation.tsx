import React from 'react';
import { ChevronDown, Search, Building2 } from 'lucide-react'; 

const SyntaxExplanation: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <details className="group">
        <summary className="flex flex-col items-center gap-2 text-lg font-medium text-gray-900 cursor-pointer">
          <span>Search query cheat sheet</span>
          <ChevronDown className="w-5 h-5 transition-transform group-open:rotate-180" />
        </summary>
        
        <div className="mt-6 space-y-8">
          {/* Google Patents */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 bg-gray-50 border-b border-gray-200">
              <Search className="h-5 w-5 text-blue-600" />
              <h3 className="font-medium text-gray-900">Google Patents</h3>
            </div>
            <div className="p-4">
              <div className="mb-4">
                <p className="text-sm text-gray-700 mb-1"><strong>Common Fields:</strong></p>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li><code>inventor:"John Doe"</code></li>
                  <li><code>assignee:"Acme Corp"</code></li>
                  <li><code>title:"solar panel"</code></li>
                  <li><code>abstract:"power saving"</code></li>
                  <li><code>cpc/H01L31/00</code> (Cooperative Patent Classification)</li>
                  <li><code>after:priority:20200101</code> (Priority date after Jan 1, 2020)</li>
                  <li><code>before:filing:20221231</code> (Filing date before Dec 31, 2022)</li>
                  <li><code>country:US</code> (Publication country)</li>
                </ul>
              </div>
              
              <div className="mb-4">
                <p className="text-sm text-gray-700 mb-1"><strong>Operators:</strong></p>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li><code>AND</code>, <code>OR</code>, <code>NOT</code> (must be uppercase)</li>
                  <li><code>"exact phrase"</code> (use double quotes)</li>
                  <li><code>(grouping terms)</code> (use parentheses)</li>
                  <li><code>word1 NEAR/5 word2</code> (word1 within 5 words of word2, order doesn't matter)</li>
                  <li><code>word1 ADJ/3 word2</code> (word1 within 3 words of word2, in order - *Advanced Search only*)</li>
                  <li><code>wildcard*</code> (matches multiple characters)</li>
                  <li><code>single?char</code> (matches single character)</li>
                </ul>
              </div>

              <div>
                <p className="text-sm text-gray-700 mb-1"><strong>Example:</strong></p>
                <div className="bg-gray-100 p-3 rounded text-sm font-mono text-gray-800">
                  (title:"AI processor" OR abstract:"neural network") AND assignee:"Tech Innovations Inc" AND cpc/G06N3/00
                </div>
              </div>
            </div>
          </div>

          {/* USPTO */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 bg-gray-50 border-b border-gray-200">
              <Building2 className="h-5 w-5 text-green-600" />
              <h3 className="font-medium text-gray-900">USPTO (Patent Public Search)</h3>
            </div>
            <div className="p-4">
              <div className="mb-4">
                <p className="text-sm text-gray-700 mb-1"><strong>Common Fields (Field Codes):</strong></p>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li><code>IN/"Doe John"</code> (Inventor)</li>
                  <li><code>AN/"Acme Corp"</code> (Assignee Name)</li>
                  <li><code>TTL/"solar panel"</code> (Title)</li>
                  <li><code>ABST/"power saving"</code> (Abstract)</li>
                  <li><code>SPEC/"energy efficient"</code> (Specification/Description)</li>
                  <li><code>ACLM/"comprising a widget"</code> (Claims)</li>
                  <li><code>CPC/H01L31/00</code> (Cooperative Patent Classification)</li>
                  <li><code>APD/&gt;1/1/2020</code> (Application Date after Jan 1, 2020)</li>
                  <li><code>ISD/&lt;12/31/2022</code> (Issue Date before Dec 31, 2022)</li>
                </ul>
              </div>
              
              <div className="mb-4">
                <p className="text-sm text-gray-700 mb-1"><strong>Operators:</strong></p>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li><code>AND</code>, <code>OR</code>, <code>NOT</code> (case insensitive)</li>
                  <li><code>"exact phrase"</code> (use double quotes)</li>
                  <li><code>(grouping terms)</code> (use parentheses)</li>
                  <li><code>word1 ADJ word2</code> (adjacent, in order)</li>
                  <li><code>word1 ADJ_ word2</code> (adjacent, any order - use underscore for Patent Center)</li>
                  <li><code>word1 SAME word2</code> (in same paragraph)</li>
                  <li><code>word1 WITH word2</code> (in same sentence)</li>
                  <li><code>$</code> (truncation for multiple characters, e.g., <code>comput$</code> matches computer, computing)</li>
                  <li><code>?</code> (wildcard for single character)</li>
                </ul>
              </div>

              <div>
                <p className="text-sm text-gray-700 mb-1"><strong>Example:</strong></p>
                <div className="bg-gray-100 p-3 rounded text-sm font-mono text-gray-800">
                  (TTL/(AI OR "artificial intelligence") AND SPEC/processor) AND AN/"Tech Innovations" AND CPC/G06N3/00
                </div>
              </div>
            </div>
          </div>
        </div>
      </details>
    </div>
  );
};

export default SyntaxExplanation;
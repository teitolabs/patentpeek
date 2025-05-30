// src/components/usptoPatents/usptoQueryBuilder.ts
import { SearchCondition, DateType, TextSearchCondition } from '../searchToolTypes'; // Added TextSearchCondition
import { GoogleLikeSearchFields } from '../googlePatents/GooglePatentsFields';

export interface UsptoSpecificSettings {
  defaultOperator: string;
  plurals: boolean;
  britishEquivalents: boolean;
  selectedDatabases: string[];
}

// Helper function (ensure these are present or add them)
const mapDateTypeToUSPTO = (dt: DateType) => {
  if(dt === 'filing') return 'APD'; // Application Date
  if(dt === 'priority') return 'PRD'; // Priority Date
  return 'ISD'; // Issue Date (Publication for USPTO context)
}
const formatDateForUSPTO = (dateStr: string) => {
  if (!dateStr) return '';
  const [year, month, day] = dateStr.split('-');
  return `${parseInt(month, 10)}/${parseInt(day, 10)}/${year}`;
}

export const generateUsptoQuery = (
    searchConditions: SearchCondition[], // Expecting a single TextSearchCondition for USPTO mode
    commonFields: GoogleLikeSearchFields,
    usptoSettings: UsptoSpecificSettings
  ): { queryStringDisplay: string; url: string } => {
    
    let setDirectives: string[] = [];
    // PPUBS Default operator is AND. Only add SET if it's different.
    if (usptoSettings.defaultOperator && usptoSettings.defaultOperator !== 'AND') {
        setDirectives.push(`DefaultOperator=${usptoSettings.defaultOperator}`);
    }
    // Always explicitly set Plural and BritishEquivalent based on checkboxes
    setDirectives.push(usptoSettings.plurals ? 'Plural=ON' : 'Plural=OFF');
    setDirectives.push(usptoSettings.britishEquivalents ? 'BritishEquivalent=ON' : 'BritishEquivalent=OFF');

    let fieldBasedQueryParts: string[] = [];
    let queryTermsPresent = false;

    searchConditions.forEach(condition => {
      if (condition.type === 'TEXT') {
        const textData = condition.data as TextSearchCondition['data']; // Type assertion
        if (textData.text.trim()) {
          queryTermsPresent = true;
          const terms = textData.text.trim().split(/\s+/).filter(Boolean);
          if (terms.length === 0) return;
          
          let processedTerms: string;
          // The 'defaultOperator' from usptoSettings applies if textData.termOperator is 'ALL' (which it is for USPTO mode)
          const joinOperatorForTextData = (textData.termOperator === 'ALL' || !textData.termOperator)
                                           ? (usptoSettings.defaultOperator || 'AND') 
                                           : textData.termOperator;

          switch (textData.termOperator) {
            case 'EXACT': processedTerms = `"${terms.join(' ')}"`; break;
            case 'ANY': processedTerms = terms.length > 1 ? `(${terms.map(t=> t.includes(" ") ? `"${t}"`: t).join(' OR ')})` : (terms[0].includes(" ") ? `"${terms[0]}"`: terms[0]); break;
            case 'NONE': processedTerms = terms.length > 1 ? `NOT (${terms.map(t => t.includes(" ") ? `"${t}"`: t).join(' OR ')})` : `NOT ${terms[0].includes(" ") ? `"${terms[0]}"`: terms[0]}`; break;
            default: // 'ALL'
               processedTerms = terms.length > 1 ? `(${terms.map(t => t.includes(" ") ? `"${t}"`: t).join(` ${joinOperatorForTextData} `)})` : (terms[0].includes(" ") ? `"${terms[0]}"`: terms[0]);
               break;
          }

          if (textData.selectedScopes.has('FT') || textData.selectedScopes.size === 0) {
            fieldBasedQueryParts.push(processedTerms);
          } else {
            const scopeQueries = Array.from(textData.selectedScopes).map(scope => {
              if (scope === 'TI') return `TTL/(${processedTerms})`;
              if (scope === 'AB') return `ABST/(${processedTerms})`;
              if (scope === 'CL') return `ACLM/(${processedTerms})`;
              if (scope === 'CPC') return `CPC/${processedTerms.replace(/[()]/g, '')}`; // USPTO CPC usually doesn't need parens for terms
              return '';
            }).filter(Boolean);
            if (scopeQueries.length > 0) fieldBasedQueryParts.push(scopeQueries.length > 1 ? `(${scopeQueries.join(' OR ')})` : scopeQueries[0]);
          }
        }
      } else if (condition.type === 'CLASSIFICATION') {
        const { cpc } = condition.data;
        if (cpc && cpc.trim()) {
            queryTermsPresent = true;
            fieldBasedQueryParts.push(`CPC/${cpc.trim()}`);
        }
      } else if (condition.type === 'NUMBERS') {
          const firstNumber = condition.data.doc_ids_text.split('\n')[0].trim();
          if (firstNumber) {
            queryTermsPresent = true;
            fieldBasedQueryParts.push(`PN/${firstNumber.replace(/patent\//i, '')}`);
          }
      }
    });
    
    // Common fields
    if (commonFields.dateFrom) { queryTermsPresent = true; fieldBasedQueryParts.push(`${mapDateTypeToUSPTO(commonFields.dateType)}/>${formatDateForUSPTO(commonFields.dateFrom)}`); }
    if (commonFields.dateTo) { queryTermsPresent = true; fieldBasedQueryParts.push(`${mapDateTypeToUSPTO(commonFields.dateType)}/<${formatDateForUSPTO(commonFields.dateTo)}`); }
    
    if (commonFields.inventors.length > 0) {
      queryTermsPresent = true;
      const invQuery = commonFields.inventors.map(inv => `"${inv.value.trim()}"`).join(' OR ');
      fieldBasedQueryParts.push(`IN/(${invQuery})`);
    }
    if (commonFields.assignees.length > 0) {
      queryTermsPresent = true;
      const asgQuery = commonFields.assignees.map(asg => `"${asg.value.trim()}"`).join(' OR ');
      fieldBasedQueryParts.push(`AN/(${asgQuery})`);
    }
    if (commonFields.cpc?.trim()) { queryTermsPresent = true; fieldBasedQueryParts.push(`CPC/${commonFields.cpc.trim()}`); }
    if (commonFields.specificTitle?.trim()) { queryTermsPresent = true; fieldBasedQueryParts.push(`TTL/("${commonFields.specificTitle.trim()}")`); }
    if (commonFields.documentId?.trim()) { queryTermsPresent = true; fieldBasedQueryParts.push(`PN/("${commonFields.documentId.trim().replace(/patent\//i, '')}")`); }

    // DB selection (counts as a query term for validity)
    if (usptoSettings.selectedDatabases && usptoSettings.selectedDatabases.length > 0) {
        queryTermsPresent = true; // Selecting databases makes the query "active"
        fieldBasedQueryParts.push(`DB=(${usptoSettings.selectedDatabases.join(' OR ')})`);
    }
    
    let finalAssembledQuery = "";
    if (setDirectives.length > 0) {
        finalAssembledQuery += `SET ${setDirectives.join(',')}`;
    }

    const mainQueryExpression = fieldBasedQueryParts.filter(Boolean).join(' AND ');

    if (mainQueryExpression) {
        finalAssembledQuery += (finalAssembledQuery ? " " : "") + mainQueryExpression;
    }
    
    let displayQuery = finalAssembledQuery.trim();

    // If no actual query terms or DB selections are present, an empty query is better than just SET commands.
    if (!queryTermsPresent) {
        displayQuery = ""; 
    }

    const url = displayQuery ? `https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsadvanced.html?query=${encodeURIComponent(displayQuery)}` : '#';
    
    return { queryStringDisplay: displayQuery, url };
};
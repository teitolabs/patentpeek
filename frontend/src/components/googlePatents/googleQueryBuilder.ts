// src/components/googlePatents/googleQueryBuilder.ts
import {
    SearchCondition,
    BackendSearchConditionPayload,
} from '../searchToolTypes';
import { GoogleLikeSearchFields } from './GooglePatentsFields'; // Import from sibling

export const generateGoogleQuery = async (
    currentSearchConditions: SearchCondition[],
    currentGoogleFields: GoogleLikeSearchFields
  ): Promise<{ queryStringDisplay: string; url: string }> => {
    const search_conditions_payload: BackendSearchConditionPayload[] = currentSearchConditions
      .map((condition: SearchCondition) => {
        let dataForPayload: any;

        switch (condition.type) {
          case 'TEXT':
            if (!condition.data.text.trim()) return null;
            dataForPayload = { ...condition.data, selectedScopes: Array.from(condition.data.selectedScopes) };
            break;
          case 'CLASSIFICATION':
            if (!condition.data.cpc.trim()) return null;
            dataForPayload = condition.data;
            break;
          case 'CHEMISTRY':
            if (!condition.data.term.trim()) return null;
            dataForPayload = { 
                term: condition.data.term, 
                operator: condition.data.operator, 
                docScope: condition.data.docScope 
            };
            break;
          case 'MEASURE':
            if (!condition.data.measurements.trim() && !condition.data.units_concepts.trim()) return null;
            dataForPayload = {
                measure_text: `${condition.data.measurements} ${condition.data.units_concepts}`.trim()
            };
            break;
          case 'NUMBERS':
            if (!condition.data.doc_ids_text.trim()) return null;
            dataForPayload = {
                doc_id: condition.data.doc_ids_text,
                number_type: condition.data.number_type,
                country_restriction: condition.data.country_restriction,
                preferred_countries_order: condition.data.preferred_countries_order,
            };
            break;
          default:
            const _exhaustiveCheck: never = condition;
            console.error("Unhandled SearchCondition type in generateGoogleQuery:", _exhaustiveCheck);
            return null;
        }
        
        return { id: condition.id, type: condition.type, data: dataForPayload };
      })
      .filter(Boolean) as BackendSearchConditionPayload[];

    const payload = {
      structured_search_conditions: search_conditions_payload.length > 0 ? search_conditions_payload : null,
      inventors: currentGoogleFields.inventors.length > 0 ? currentGoogleFields.inventors.map(inv => inv.value) : null,
      assignees: currentGoogleFields.assignees.length > 0 ? currentGoogleFields.assignees.map(asg => asg.value) : null,
      after_date: currentGoogleFields.dateFrom || null,
      after_date_type: currentGoogleFields.dateFrom ? currentGoogleFields.dateType : null,
      before_date: currentGoogleFields.dateTo || null,
      before_date_type: currentGoogleFields.dateTo ? currentGoogleFields.dateType : null,
      patent_offices: currentGoogleFields.patentOffices.length > 0 ? currentGoogleFields.patentOffices : null,
      languages: currentGoogleFields.languages.length > 0 ? currentGoogleFields.languages : null,
      status: currentGoogleFields.status || null,
      patent_type: currentGoogleFields.patentType || null,
      litigation: currentGoogleFields.litigation || null,
      dedicated_cpc: currentGoogleFields.cpc?.trim() || null,
      dedicated_title: currentGoogleFields.specificTitle?.trim() || null,
      dedicated_document_id: currentGoogleFields.documentId?.trim() || null,
    };

    try {
      const response = await fetch('/api/generate-google-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      return {
        queryStringDisplay: result.query_string_display || '',
        url: result.url || '#',
      };
    } catch (error) {
        console.error("Failed to fetch Google query details:", error);
        const errorMessage = error instanceof Error ? error.message : "Error generating query from server.";
        return { queryStringDisplay: errorMessage, url: "#" };
    }
  };
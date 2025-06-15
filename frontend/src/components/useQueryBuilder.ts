// src/components/useQueryBuilder.ts
import { useState, useEffect, useCallback } from 'react';
import { PatentFormat } from '../types';
import { 
    // --- FIX: Removed unused TextSearchCondition import ---
    SearchCondition, GoogleLikeSearchFields, 
    UsptoSpecificSettings 
} from './searchToolTypes';
import { generateQuery, parseQuery } from './googlePatents/googleApi';

// Helper to manage the empty text box at the end of the list
const manageSearchConditionInputs = (conditions: SearchCondition[]): SearchCondition[] => {
    // Filter out any empty conditions except for the last one
    let filteredConditions = conditions.filter((cond, index) => {
        if (cond.data.text.trim() === '') {
            // Keep this empty one only if it's the last one
            return index === conditions.length - 1;
        }
        return true;
    });

    // Ensure there's always one empty box at the end if the last one is not empty
    const lastCondition = filteredConditions[filteredConditions.length - 1];
    if (!lastCondition || lastCondition.data.text.trim() !== '') {
        filteredConditions.push({
            id: crypto.randomUUID(),
            type: 'TEXT',
            data: { text: '', error: null }
        });
    }

    // Handle the case where the list becomes completely empty
    if (filteredConditions.length === 0) {
        filteredConditions.push({
            id: crypto.randomUUID(),
            type: 'TEXT',
            data: { text: '', error: null }
        });
    }
    return filteredConditions;
};


export const useQueryBuilder = (activeFormat: PatentFormat) => {
    // --- STATE MANAGEMENT ---
    // All "source of truth" state is managed here.
    const [searchConditions, setSearchConditions] = useState<SearchCondition[]>(
        () => manageSearchConditionInputs([])
    );
    const [googleLikeFields, setGoogleLikeFields] = useState<GoogleLikeSearchFields>({
        dateFrom: '', dateTo: '', dateType: 'publication', inventors: [], assignees: [], patentOffices: [], languages: [], status: '', patentType: '', litigation: '',
    });
    const [usptoSpecificSettings, setUsptoSpecificSettings] = useState<UsptoSpecificSettings>({
        defaultOperator: 'AND', plurals: false, britishEquivalents: true, selectedDatabases: ['US-PGPUB', 'USPAT', 'USOCR'], highlights: 'SINGLE_COLOR', showErrors: true,
    });
    
    // --- DERIVED STATE ---
    // These are derived from the source of truth state above.
    const [mainQueryValue, setMainQueryValue] = useState('');
    const [queryLinkHref, setQueryLinkHref] = useState('#');

    // --- EFFECT FOR RE-GENERATION ---
    // This effect runs whenever the source-of-truth state changes,
    // automatically regenerating the query string. This is the "forward" flow.
    useEffect(() => {
        const generate = async () => {
            const result = await generateQuery(activeFormat, searchConditions, googleLikeFields, usptoSpecificSettings);
            setMainQueryValue(result.queryStringDisplay);
            setQueryLinkHref(result.url);
        };
        generate();
    }, [searchConditions, googleLikeFields, usptoSpecificSettings, activeFormat]);

    // --- HANDLERS TO MODIFY STATE ---
    // These functions are the public API of our hook. Components will call them.
    const onFieldChange = useCallback(<K extends keyof GoogleLikeSearchFields>(field: K, value: GoogleLikeSearchFields[K]) => {
        setGoogleLikeFields(prev => ({ ...prev, [field]: value }));
    }, []);

    const updateSearchConditionText = useCallback((id: string, newText: string) => {
        setSearchConditions(prev => {
            const updated = prev.map(sc => 
                sc.id === id ? { ...sc, data: { ...sc.data, text: newText, error: null /* Validation can be added here */ } } : sc
            );
            return manageSearchConditionInputs(updated);
        });
    }, []);

    const removeSearchCondition = useCallback((id: string) => {
        setSearchConditions(prev => manageSearchConditionInputs(prev.filter(sc => sc.id !== id)));
    }, []);

    // --- PARSING LOGIC ---
    // This handles the "backward" flow: from a raw string to structured state.
    const handleParseAndApply = useCallback(async (queryString: string) => {
        if (!queryString.trim()) {
            // If user clears the input, reset the state
            setSearchConditions(manageSearchConditionInputs([]));
            setGoogleLikeFields({ dateFrom: '', dateTo: '', dateType: 'publication', inventors: [], assignees: [], patentOffices: [], languages: [], status: '', patentType: '', litigation: '' });
            return;
        }
        try {
            const result = await parseQuery(activeFormat, queryString);
            // Directly set the state from the parsed result. The useEffect will handle regeneration.
            setSearchConditions(manageSearchConditionInputs(result.searchConditions));
            setGoogleLikeFields(result.googleLikeFields);
            setUsptoSpecificSettings(result.usptoSpecificSettings);
        } catch (error) {
            console.error("Parsing failed:", error);
            setMainQueryValue(`Error parsing query: ${(error as Error).message}`);
        }
    }, [activeFormat]);

    // --- RETURN THE PUBLIC API OF THE HOOK ---
    return {
        // State
        mainQueryValue,
        queryLinkHref,
        searchConditions,
        googleLikeFields,
        usptoSpecificSettings,

        // Handlers
        setGoogleLikeFields, // Exposing the full setter for complex cases like parsing
        onFieldChange,
        updateSearchConditionText,
        removeSearchCondition,
        handleParseAndApply,
        setSearchConditions, // Exposing for individual term parsing
    };
};
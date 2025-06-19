// src/components/useQueryBuilder.ts
import { useState, useEffect, useCallback } from 'react';
import { PatentFormat } from '../types';
import { 
    SearchCondition, GoogleLikeSearchFields, 
    UsptoSpecificSettings 
} from './searchToolTypes';
import { generateQuery, parseQuery } from './googlePatents/googleApi';
import { generateUsptoQuery } from './usptoPatents/usptoQueryBuilder';


// Helper to manage the empty text box at the end of the list
const manageSearchConditionInputs = (conditions: SearchCondition[]): SearchCondition[] => {
    let filteredConditions = conditions.filter((cond, index) => {
        if (cond.data.text.trim() === '') {
            return index === conditions.length - 1;
        }
        return true;
    });

    const lastCondition = filteredConditions[filteredConditions.length - 1];
    if (!lastCondition || lastCondition.data.text.trim() !== '') {
        filteredConditions.push({
            id: crypto.randomUUID(),
            type: 'TEXT',
            data: { text: '', error: null }
        });
    }

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
    const [searchConditions, setSearchConditions] = useState<SearchCondition[]>(
        () => manageSearchConditionInputs([])
    );
    const [googleLikeFields, setGoogleLikeFields] = useState<GoogleLikeSearchFields>({
        dateFrom: '', dateTo: '', dateType: 'publication', inventors: [], assignees: [], patentOffices: [], languages: [], status: '', patentType: '', litigation: '',
    });
    // --- THIS IS THE FIX ---
    // Updated the initial state for USPTO settings per your request.
    const [usptoSpecificSettings, setUsptoSpecificSettings] = useState<UsptoSpecificSettings>({
        defaultOperator: 'OR',
        plurals: true,
        britishEquivalents: true,
        selectedDatabases: ['US-PGPUB', 'USPAT', 'USOCR'],
        highlights: 'SINGLE_COLOR',
        showErrors: true,
    });
    const [usptoQuery, setUsptoQuery] = useState('');
    
    // --- DERIVED STATE ---
    const [mainQueryValue, setMainQueryValue] = useState('');
    const [queryLinkHref, setQueryLinkHref] = useState('#');
    const [ast, setAst] = useState<Record<string, any> | null>(null);

    // --- EFFECT FOR RE-GENERATION ---
    useEffect(() => {
        if (activeFormat === 'google') {
            const generate = async () => {
                const result = await generateQuery(activeFormat, searchConditions, googleLikeFields, usptoSpecificSettings);
                setMainQueryValue(result.queryStringDisplay);
                setQueryLinkHref(result.url);
                setAst(result.ast);
            };
            generate();
        } else { // activeFormat is 'uspto'
            const { url } = generateUsptoQuery(usptoQuery, usptoSpecificSettings);
            setQueryLinkHref(url);
            setMainQueryValue(usptoQuery); // For USPTO, the main value is the raw query
        }
    }, [searchConditions, googleLikeFields, usptoSpecificSettings, activeFormat, usptoQuery]);

    // --- HANDLERS TO MODIFY STATE ---
    const onFieldChange = useCallback(<K extends keyof GoogleLikeSearchFields>(field: K, value: GoogleLikeSearchFields[K]) => {
        setGoogleLikeFields(prev => ({ ...prev, [field]: value }));
    }, []);

    const onUsptoFieldChange = useCallback(<K extends keyof UsptoSpecificSettings>(field: K, value: UsptoSpecificSettings[K]) => {
        setUsptoSpecificSettings(prev => ({ ...prev, [field]: value }));
    }, []);


    const updateSearchConditionText = useCallback((id: string, newText: string) => {
        setSearchConditions(prev => {
            const updated = prev.map(sc => 
                sc.id === id ? { ...sc, data: { ...sc.data, text: newText, error: null } } : sc
            );
            return manageSearchConditionInputs(updated);
        });
    }, []);

    const removeSearchCondition = useCallback((id: string) => {
        setSearchConditions(prev => manageSearchConditionInputs(prev.filter(sc => sc.id !== id)));
    }, []);

    // --- PARSING LOGIC ---
    const handleParseAndApply = useCallback(async (queryString: string) => {
        if (activeFormat === 'uspto') {
            setUsptoQuery(queryString);
            return;
        }

        if (!queryString.trim()) {
            setSearchConditions(manageSearchConditionInputs([]));
            setGoogleLikeFields({ dateFrom: '', dateTo: '', dateType: 'publication', inventors: [], assignees: [], patentOffices: [], languages: [], status: '', patentType: '', litigation: '' });
            return;
        }
        try {
            const result = await parseQuery(activeFormat, queryString);
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
        ast,
        searchConditions,
        googleLikeFields,
        usptoSpecificSettings,
        usptoQuery,

        // Handlers
        setGoogleLikeFields,
        onFieldChange,
        setUsptoSpecificSettings,
        onUsptoFieldChange,
        setUsptoQuery,
        updateSearchConditionText,
        removeSearchCondition,
        handleParseAndApply,
        setSearchConditions,
    };
};
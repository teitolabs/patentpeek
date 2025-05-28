// Expanded list of common words and patent-specific jargon to exclude
const COMMON_STOP_WORDS = new Set<string>([ // Explicitly type the Set as Set<string>
  // Standard English stop words
  "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
  "have", "has", "had", "do", "does", "did", "will", "would", "should", "can",
  "could", "may", "might", "must", "of", "at", "by", "for", "with", "about",
  "against", "between", "into", "through", "during", "before", "after", "above",
  "below", "to", "from", "up", "down", "in", "out", "on", "off", "over",
  "under", "again", "further", "then", "once", "here", "there", "when", "where",
  "why", "how", "all", "any", "both", "each", "few", "more", "most", "other",
  "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
  "too", "very", "s", "t", "just", "don", "should've", "now", "d", "ll", "m", "o", "re", "ve", "y",
  // Patent-specific or common technical jargon to exclude from simple keyword extraction
  "method", "system", "apparatus", "device", "component", "module",
  "means", "step", "plurality", "predetermined", "thereof", "herein",
  "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
  "wherein", "whereby", "thereby", "further", "includes", "comprises", "comprising",
  "based on", "such as", "according to", "respectively", "related to",
  "alternatively", "optionally", "example", "figure", "illustrates", "embodiment"
]);

// Simple stemming function (Porter stemmer is more complex, this is a basic suffix stripper)
function simpleStem(word: string): string {
  const Suffixes = ['s', 'es', 'ed', 'ing', 'ly', 'er', 'ion', 'ions', 'ive']; // Simplified
  for (const suffix of Suffixes) {
    // Ensure base word is not too short and suffix actually matches
    if (word.length > suffix.length + 2 && word.endsWith(suffix)) { 
      return word.slice(0, -suffix.length);
    }
  }
  return word;
}

export async function generatePatentQuery(description: string, keywordCount: number = 7): Promise<string> {
  try {
    const words: string[] = description.toLowerCase() // Ensure words is explicitly string[]
      .replace(/[^\w\s-]/gi, '') // Allow hyphens in words, remove other punctuation
      .split(/\s+/)
      .map(word => simpleStem(word)) // Apply simple stemming
      .filter(word => 
        word.length > 2 && // Min word length
        !COMMON_STOP_WORDS.has(word) && // word is now string, COMMON_STOP_WORDS is Set<string>
        !/^\d+$/.test(word) // Exclude numbers
      );

    // Count word frequencies
    const wordFrequencies: Record<string, number> = {};
    for (const word of words) {
      wordFrequencies[word] = (wordFrequencies[word] || 0) + 1;
    }

    // Get unique words, sort by frequency (desc), then alphabetically for ties
    const sortedUniqueWords = Array.from(new Set(words))
      .sort((a, b) => {
        const freqDiff = wordFrequencies[b] - wordFrequencies[a];
        if (freqDiff !== 0) return freqDiff;
        return a.localeCompare(b); // Alphabetical for same frequency
      })
      .slice(0, keywordCount); // Take top N keywords

    if (sortedUniqueWords.length === 0) return '';
    
    return sortedUniqueWords.join(' ADJ '); 

  } catch (error) {
    console.error('Error generating query:', error);
    return '';
  }
}
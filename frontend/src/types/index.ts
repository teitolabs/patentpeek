// src/types.ts
export type PatentFormat = 'google' | 'uspto' | 'unknown';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'system';
  format?: PatentFormat; // The format of 'text'
  originalText?: string; // The text before conversion
  originalFormat?: PatentFormat; // The format of 'originalText'
}

export interface ConversionResult {
  text: string;
  format: PatentFormat;
}
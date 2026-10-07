export interface IndianLanguage {
  code: string;
  name: string;
  nativeName: string;
  script: string;
  family: 'Indo-Aryan' | 'Dravidian';
  speakersMillion: number;
  sampleSentence: string;
  phonemeHighlight: string;
}

export const SUPPORTED_LANGUAGES: IndianLanguage[] = [
  {
    code: 'hi',
    name: 'Hindi',
    nativeName: 'हिन्दी',
    script: 'Devanagari',
    family: 'Indo-Aryan',
    speakersMillion: 602,
    sampleSentence: 'नमस्ते, निविमा में आपका स्वागत है।',
    phonemeHighlight: 'कण्ठ्य (Velar) & मूर्धन्य (Retroflex)'
  },
  {
    code: 'ta',
    name: 'Tamil',
    nativeName: 'தமிழ்',
    script: 'Tamil',
    family: 'Dravidian',
    speakersMillion: 86,
    sampleSentence: 'வணக்கம், நிவிமா உங்களை அன்புடன் வரவேற்கிறது.',
    phonemeHighlight: 'ழ (zh / ɻ), ள (ḷ / ɭ), ற (ṟ / r)'
  },
  {
    code: 'te',
    name: 'Telugu',
    nativeName: 'తెలుగు',
    script: 'Telugu',
    family: 'Dravidian',
    speakersMillion: 96,
    sampleSentence: 'నమస్కారం, నివిమా ప్లాట్‌ఫారమ్‌కు స్వాగతం.',
    phonemeHighlight: 'ట (ṭ / ʈ), డ (ḍ / ɖ), ణ (ṇ / ɳ)'
  },
  {
    code: 'kn',
    name: 'Kannada',
    nativeName: 'ಕನ್ನಡ',
    script: 'Kannada',
    family: 'Dravidian',
    speakersMillion: 45,
    sampleSentence: 'ನಮಸ್ಕಾರ, ನಿವಿಮಾ ತಾಣಕ್ಕೆ ಸುಸ್ವಾಗತ.',
    phonemeHighlight: 'ಳ (ḷ / ɭ), ಣ (ṇ / ɳ), ಠ (ṭh / ʈʰ)'
  },
  {
    code: 'ml',
    name: 'Malayalam',
    nativeName: 'മലയാളം',
    script: 'Malayalam',
    family: 'Dravidian',
    speakersMillion: 38,
    sampleSentence: 'നമസ്കാരം, നിവിമയിലേക്ക് സ്വാഗതം.',
    phonemeHighlight: 'ഴ (zh / ɻ), റ (ṟ), ള (ḷ)'
  },
  {
    code: 'bn',
    name: 'Bengali',
    nativeName: 'বাংলা',
    script: 'Bengali',
    family: 'Indo-Aryan',
    speakersMillion: 272,
    sampleSentence: 'নমস্কার, নিভিমাতে আপনাকে স্বাগতম।',
    phonemeHighlight: 'ট (ṭ / ʈ), ড (ḍ / ɖ), ড় (ṛ / ɽ)'
  },
  {
    code: 'mr',
    name: 'Marathi',
    nativeName: 'मराठी',
    script: 'Devanagari',
    family: 'Indo-Aryan',
    speakersMillion: 95,
    sampleSentence: 'नमस्कार, निविमा मध्ये आपले स्वागत आहे.',
    phonemeHighlight: 'ळ (ḷ / ɭ), ऱ (ṟ), ण (ṇ)'
  },
  {
    code: 'gu',
    name: 'Gujarati',
    nativeName: 'ગુજરાતી',
    script: 'Gujarati',
    family: 'Indo-Aryan',
    speakersMillion: 62,
    sampleSentence: 'નમસ્તે, નિવિમામાં આપનું સ્વાગત છે.',
    phonemeHighlight: 'ળ (ḷ / ɭ), ટ (ṭ / ʈ), ડ (ḍ / ɖ)'
  },
  {
    code: 'pa',
    name: 'Punjabi',
    nativeName: 'ਪੰਜਾਬੀ',
    script: 'Gurmukhi',
    family: 'Indo-Aryan',
    speakersMillion: 125,
    sampleSentence: 'ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ, ਨਿਵਿਮਾ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ।',
    phonemeHighlight: 'ਟ (ṭ / ʈ), ਡ (ḍ / ɖ), ਣ (ṇ / ɳ)'
  },
  {
    code: 'or',
    name: 'Odia',
    nativeName: 'ଓଡ଼ିଆ',
    script: 'Odia',
    family: 'Indo-Aryan',
    speakersMillion: 39,
    sampleSentence: 'ନମସ୍କାର, ନିଭିମା କୁ ଆପଣଙ୍କୁ ସ୍ୱାଗତ।',
    phonemeHighlight: 'ଳ (ḷ / ɭ), ଡ (ḍ / ɖ), ଢ (ḍh / ɖʱ)'
  }
];

export interface VisemeBlendshape {
  name: string;
  symbol: string;
  description: string;
  jawOpen: number;
  lipPressor: number;
  cheekRaiser: number;
  lipTightener: number;
  tongueCurl: number;
  westernLimitation: string;
}

export const RETROFLEX_VISEMES: VisemeBlendshape[] = [
  {
    name: 'Dravidian Retroflex Plosive',
    symbol: 'ʈ (ట / ட / ट)',
    description: 'Sub-apical palatal contact with retracted lower jaw and lateral cheek tension',
    jawOpen: 0.38,
    lipPressor: 0.15,
    cheekRaiser: 0.65,
    lipTightener: 0.30,
    tongueCurl: 0.95,
    westernLimitation: 'Wav2Lip / CMU collapses this into English alveolar /t/, resulting in flat anterior lip shape.'
  },
  {
    name: 'Voiced Retroflex Stop',
    symbol: 'ɖ (డ / డ / ड)',
    description: 'Retracted tongue tip behind alveolar ridge, partial lip compression',
    jawOpen: 0.42,
    lipPressor: 0.20,
    cheekRaiser: 0.58,
    lipTightener: 0.35,
    tongueCurl: 0.90,
    westernLimitation: 'Treated as English /d/; causes visual desync on syllable onset in Telugu and Tamil.'
  },
  {
    name: 'Retroflex Nasal',
    symbol: 'ɳ (ణ / ண / ण)',
    description: 'Nasal resonance accompanied by curled retroflex tongue and lowered soft palate',
    jawOpen: 0.32,
    lipPressor: 0.25,
    cheekRaiser: 0.70,
    lipTightener: 0.40,
    tongueCurl: 0.92,
    westernLimitation: 'Mapped to generic alveolar /n/; misses visible cheek raiser activation.'
  },
  {
    name: 'Retroflex Approximant',
    symbol: 'ɻ (ழ / ഴ)',
    description: 'Distinctive Tamil/Malayalam liquid consonant with curling tongue toward post-alveolar groove',
    jawOpen: 0.35,
    lipPressor: 0.10,
    cheekRaiser: 0.80,
    lipTightener: 0.50,
    tongueCurl: 1.0,
    westernLimitation: 'Completely nonexistent in CMU/Western phonesets. All other models distort this viseme.'
  }
];

export interface QCScoreBreakdown {
  syncNet: number;
  csim: number;
  psnr: number;
  temporalVariance: number;
  verdict: 'PASS' | 'REVIEW' | 'REJECT';
}

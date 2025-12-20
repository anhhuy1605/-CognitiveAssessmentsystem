export interface ResearchPaper {
  id: string;
  title: string;
  authors: string[];
  journal?: string;
  year: number;
  abstract: string;
  url?: string;
  tags: string[];
  category?: 'research' | 'treatment' | 'technology' | 'vietnamese';
  relevance?: 'high' | 'medium' | 'low';
}

export const researchPapers: ResearchPaper[] = [
  {
    id: 'adress-2020',
    title: 'The ADReSS Challenge 2020: Alzheimer\'s Dementia Recognition through Spontaneous Speech',
    authors: ['Saturnino Luz', 'Daniel Goncalves', 'Sergio Gonzalez', 'Marta Vazquez'],
    journal: 'INTERSPEECH 2020',
    year: 2020,
    abstract: 'The ADReSS Challenge aims to develop technology that can assist in the automated recognition of Alzheimer\'s Dementia (AD) through spontaneous speech. We describe the design of the challenge, the data collection process, and baseline results.',
    url: 'https://www.isca-speech.org/archive/interspeech_2020/luz20_interspeech.html',
    tags: ['speech analysis', 'dementia detection', 'machine learning'],
    category: 'research',
    relevance: 'high'
  },
  {
    id: 'fraser-2021',
    title: 'Predicting MCI-to-AD Progression Using Speech Disorder Features',
    authors: ['Kathleen Fraser', 'Saturnino Luz', 'Daniel Blackburn'],
    journal: 'Frontiers in Aging Neuroscience',
    year: 2021,
    abstract: 'This study investigates the use of speech disorder features to predict progression from mild cognitive impairment (MCI) to Alzheimer\'s disease (AD). Results show 78% accuracy in predicting MCI-to-AD transition.',
    url: 'https://www.frontiersin.org/articles/10.3389/fnagi.2021.742137/full',
    tags: ['MCI progression', 'speech disorders', 'prediction'],
    category: 'research',
    relevance: 'high'
  },
  {
    id: 'dementiabank-pause',
    title: 'Pause Duration and Semantic Coherence in Dementia Speech',
    authors: ['Heidi Christensen', 'Daniel Blackburn', 'Saturnino Luz'],
    journal: 'Computer Speech & Language',
    year: 2021,
    abstract: 'Analysis of pause duration and semantic coherence in speech samples from DementiaBank reveals significant differences between healthy controls and individuals with dementia.',
    url: 'https://www.sciencedirect.com/science/article/pii/S0885230821000036',
    tags: ['pause duration', 'semantic coherence', 'DementiaBank'],
    category: 'research',
    relevance: 'high'
  },
  {
    id: 'vietnamese-speech-analysis',
    title: 'Acoustic and Linguistic Features for Vietnamese Dementia Detection',
    authors: ['Local Research Team', 'Preliminary Study'],
    journal: 'Vietnamese Journal of Cognitive Science',
    year: 2024,
    abstract: 'Preliminary investigation into adapting speech analysis techniques for Vietnamese speakers with dementia, considering tonal features and linguistic patterns specific to Vietnamese.',
    tags: ['Vietnamese', 'tone analysis', 'cultural adaptation'],
    category: 'vietnamese',
    relevance: 'high'
  },
  {
    id: 'digital-biomarkers',
    title: 'Digital Biomarkers in Alzheimer\'s Disease',
    authors: ['Rhoda Au', 'Jaehoon Lee', 'Vagelis Hristidis'],
    journal: 'Alzheimer\'s & Dementia',
    year: 2022,
    abstract: 'Review of digital biomarkers for Alzheimer\'s disease, including speech and language-based markers, wearable sensors, and smartphone applications.',
    url: 'https://alz-journals.onlinelibrary.wiley.com/doi/10.1002/alz.12529',
    tags: ['digital biomarkers', 'review', 'technology'],
    category: 'technology',
    relevance: 'medium'
  },
  {
    id: 'speech-therapy-ad',
    title: 'Speech-Language Therapy for Alzheimer\'s Disease',
    authors: ['Anastasia Raymer', 'Jamie Azios'],
    journal: 'Seminars in Speech and Language',
    year: 2021,
    abstract: 'Evidence-based review of speech-language therapy interventions for individuals with Alzheimer\'s disease, focusing on communication strategies and caregiver training.',
    tags: ['speech therapy', 'intervention', 'caregiver support'],
    category: 'treatment',
    relevance: 'medium'
  },
  {
    id: 'voice-analysis-review',
    title: 'Voice Analysis for Detection of Parkinson\'s and Alzheimer\'s Diseases',
    authors: ['Mahdi Khazaee', 'Reza Zarei'],
    journal: 'Journal of Medical Signals and Sensors',
    year: 2023,
    abstract: 'Comprehensive review of voice analysis techniques for detecting Parkinson\'s and Alzheimer\'s diseases, including acoustic features and machine learning approaches.',
    tags: ['voice analysis', 'review', 'multiple diseases'],
    category: 'research',
    relevance: 'medium'
  },
  {
    id: 'home-monitoring',
    title: 'Home-Based Monitoring of Cognitive Health Using Speech',
    authors: ['Sarah Reimer', 'Kristina Lundholm Fors'],
    journal: 'Frontiers in Digital Health',
    year: 2023,
    abstract: 'Exploration of home-based speech monitoring for early detection of cognitive decline, discussing implementation challenges and potential benefits.',
    tags: ['home monitoring', 'early detection', 'implementation'],
    category: 'technology',
    relevance: 'high'
  }
];

export const rssSources = [
  {
    name: 'Alzheimer\'s Research & Therapy',
    url: 'https://alzres.biomedcentral.com/articles/most-recent/rss',
    category: 'research'
  },
  {
    name: 'Alzheimer\'s & Dementia Journal',
    url: 'https://alz-journals.onlinelibrary.wiley.com/feed/15525279/most-recent',
    category: 'research'
  },
  {
    name: 'Frontiers in Aging Neuroscience',
    url: 'https://www.frontiersin.org/journals/aging-neuroscience/rss',
    category: 'research'
  }
];

export const filterOptions = [
  { value: 'all', label: 'Tất cả' },
  { value: 'research', label: 'Nghiên cứu' },
  { value: 'treatment', label: 'Điều trị' },
  { value: 'technology', label: 'Công nghệ' },
  { value: 'vietnamese', label: 'Tiếng Việt' }
];

// The base URL of your Python backend
const API_URL = 'http://127.0.0.1:8000';

// --- THIS IS THE MISSING FUNCTION ---
/**
 * Calls the simple search endpoint.
 */
export const searchArticles = async (query) => {
    const response = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    });
    if (!response.ok) throw new Error('Network response was not ok.');
    return response.json();
};
// --- END OF MISSING FUNCTION ---


/**
 * Calls the initial analysis endpoint.
 */
export const analyzeQuery = async (query) => {
    const response = await fetch(`${API_URL}/analyze-query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    });
    if (!response.ok) throw new Error('Network response was not ok.');
    return response.json();
};

/**
 * Calls the deep analysis endpoint with a specific ID.
 */
export const getDeepAnalysis = async (analysisId) => {
    const response = await fetch(`${API_URL}/deep-analysis/${analysisId}`);
    if (!response.ok) throw new Error('Network response was not ok.');
    return response.json();
};

/**
 * Calls the narrative comparison endpoint.
 */
export const compareNarratives = async (intended_truth, media_text) => {
    const response = await fetch(`${API_URL}/compare-narratives`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intended_truth, media_text })
    });
    if (!response.ok) throw new Error('Network response was not ok.');
    return response.json();
};

/**
 * Calls the perception trend analysis endpoint.
 */
export const analyzePerceptionTrend = async (keywords, time_period_days = 30) => {
    const response = await fetch(`${API_URL}/analyze-perception-trend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keywords, time_period_days, granularity_days: 7 })
    });
    if (!response.ok) throw new Error('Network response was not ok.');
    return response.json();
};
 
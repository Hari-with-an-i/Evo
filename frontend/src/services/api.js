// The base URL of your Python backend
const API_URL = 'http://127.0.0.1:8000';

/**
 * Invokes the Brain Agent with a natural language prompt.
 * @param {string} prompt - The user's input/query.
 * @returns {Promise<object>} - The JSON response containing 'final_response'.
 */
export const invokeBrain = async (prompt) => {
    try {
        const response = await fetch(`${API_URL}/brain/invoke`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: prompt })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Network response was not ok');
        }

        return response.json();
    } catch (error) {
        console.error("API Call Error:", error);
        throw error;
    }
};

// Deprecated specific endpoints - mapped to Brain calls for backward compatibility if needed, 
// or simply replaced in the components.
// We will replace usage in components, so we don't strictly need them here, 
// but keeping wrapper functions might keep components cleaner.

export const searchArticles = async (query) => {
    return invokeBrain(`Search for recent news about: ${query}`);
};

export const analyzePerceptionTrend = async (keywords, time_period_days = 30) => {
    return invokeBrain(`Analyze the perception trend of '${keywords}' over the last ${time_period_days} days.`);
};

export const generateCounterSpeech = async (statement) => {
    return invokeBrain(`Generate counter speech and arguments against this statement: "${statement}"`);
};

export const generateNarrativeReport = async (topic) => {
    return invokeBrain(`Generate a comprehensive narrative report on: ${topic}`);
};

export const compareNarratives = async (intended_truth, media_text) => {
    // Determine how to handle structured response expectation later. 
    // For now, returning the brain response as a simple object to prevent crashes, 
    // assuming the component might display the text if we adjust it.
    // Or we can try to prompt the brain to return JSON, but that's unreliable without a structured output parser.
    // Let's just return the text in a way that might be displayed, or at least doesn't crash the build.
    return invokeBrain(`Compare this intended truth: "${intended_truth}" with this media text: "${media_text}". Highlight narrative gaps and misinterpreted points.`);
};

export const queryGroundTruth = async (query) => {
    return invokeBrain(`Query the knowledge base for: ${query}`);
};

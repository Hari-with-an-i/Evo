import React from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

function SentimentChart({ analyticsData }) {
    // --- THIS IS THE FIX ---
    // If analyticsData is not yet available, don't try to render the chart.
    // Instead, show a loading message or nothing at all.
    if (!analyticsData || Object.keys(analyticsData).length === 0) {
        return <div>Loading chart data...</div>; // Or you can return null
    }
    // --- END OF FIX ---

    const labels = Object.keys(analyticsData).sort();
    const dataPoints = labels.map(label => analyticsData[label].average_sentiment_score);

    const data = {
        labels,
        datasets: [{
            label: 'Average Sentiment Trend',
            data: dataPoints,
            borderColor: 'rgb(24, 119, 242)',
            backgroundColor: 'rgba(24, 119, 242, 0.5)',
        }]
    };

    const options = {
        responsive: true,
        plugins: { legend: { position: 'top' }, title: { display: true, text: 'Sentiment Over Time' } },
        scales: { y: { min: -1, max: 1 } }
    };

    return <Line options={options} data={data} />;
}

export default SentimentChart;
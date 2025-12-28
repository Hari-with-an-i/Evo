import React from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function SentimentChart({ analyticsData }) {
  if (!analyticsData || Object.keys(analyticsData).length === 0) {
    return <div className="text-gray-400 text-sm">Loading chart...</div>;
  }

  const labels = Object.keys(analyticsData).sort();
  const dataPoints = labels.map(
    (label) => analyticsData[label].average_sentiment_score
  );

  const data = {
    labels,
    datasets: [
      {
        label: "Average Sentiment Trend",
        data: dataPoints,
        borderColor: "#4dabf7",
        backgroundColor: "rgba(77, 171, 247, 0.4)",
        tension: 0.3
      }
    ]
  };

  const options = {
    responsive: true,
    animation: {
      duration: 900,
      easing: "easeOutQuart"
    },
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Sentiment Over Time" }
    },
    scales: {
      y: { min: -1, max: 1 }
    }
  };

  return <Line options={options} data={data} />;
}

export default SentimentChart;

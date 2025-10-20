// src/components/WeeklyTrends.jsx
import React, { useState, useMemo } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip as ChartTooltip, Legend as ChartLegend, BarElement } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, ChartTooltip, ChartLegend);

const styles = {
    sectionTitle: { fontSize: '2em', marginBottom: '20px' },
    kpiGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '40px', marginBottom: '40px' },
    kpiCard: { padding: '20px', backgroundColor: '#374151', borderRadius: '8px' },
    sliderContainer: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '20px', margin: '20px 0 40px' },
    sliderButton: { padding: '10px 15px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' },
    sliderLabel: { fontSize: '1.2em' },
};

// Helper to format date from YYYYMMDD to a readable format
const formatDate = (dateString) => {
    const year = dateString.substring(0, 4);
    const month = dateString.substring(4, 6);
    const day = dateString.substring(6, 8);
    return `${new Date(`${year}-${month}-${day}`).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
};

const WEEK_WINDOW_SIZE = 7;

const WeeklyTrends = ({ weeklyData }) => {
    // weeklyData is sorted from latest to oldest
    const [windowIndex, setWindowIndex] = useState(0); 

    // Calculate the current window data
    const currentWindowData = useMemo(() => {
        const startIndex = windowIndex * WEEK_WINDOW_SIZE;
        // Slice from the sorted (latest to oldest) data, then reverse to show oldest to latest on chart
        return weeklyData.slice(startIndex, startIndex + WEEK_WINDOW_SIZE).reverse();
    }, [weeklyData, windowIndex]);

    const totalWindows = Math.ceil(weeklyData.length / WEEK_WINDOW_SIZE);
    
    // --- Chart Data Preparation ---

    const labels = currentWindowData.map(w => formatDate(w.week_start_date));
    const interactionVolumes = currentWindowData.map(w => w.interaction_volume);
    
    // KPI 1 & 2: Line Graph Data
    const trendLineData = {
        labels,
        datasets: [
            {
                label: 'Total Interactions',
                data: interactionVolumes,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                fill: true,
                yAxisID: 'y1',
            },
            {
                label: 'Active Users',
                // NOTE: The schema is missing Active Users per week, so we'll simulate it for now.
                data: interactionVolumes.map(v => Math.round(v * 0.5)), 
                borderColor: '#10b981',
                backgroundColor: 'transparent',
                pointBorderColor: '#10b981',
                yAxisID: 'y2',
            },
        ],
    };

    // KPI 4: Stacked Bar Chart Data (Language Distribution with Modality Stack)
    const languageData = useMemo(() => {
        const aggregated = {};
        
        currentWindowData.forEach(week => {
            week.language_distribution.forEach(langEntry => {
                if (!aggregated[langEntry.lang]) {
                    aggregated[langEntry.lang] = { total: 0, voice: 0, text: 0 };
                }
                aggregated[langEntry.lang].total += langEntry.interactions;
                aggregated[langEntry.lang].voice += langEntry.voice;
                aggregated[langEntry.lang].text += (langEntry.interactions - langEntry.voice);
            });
        });

        const sortedLangs = Object.entries(aggregated)
            .sort(([, a], [, b]) => b.total - a.total)
            .slice(0, 5); // Top 5 for the chart

        const chartLabels = sortedLangs.map(([lang]) => lang);
        const voiceData = sortedLangs.map(([, data]) => data.voice);
        const textData = sortedLangs.map(([, data]) => data.text);

        return {
            labels: chartLabels,
            datasets: [
                {
                    label: 'Voice Interactions',
                    data: voiceData,
                    backgroundColor: '#3b82f6', // Accent Blue
                },
                {
                    label: 'Text Interactions',
                    data: textData,
                    backgroundColor: '#9ca3af', // Gray for text
                },
            ],
        };
    }, [currentWindowData]);

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                stacked: true,
                grid: { color: 'rgba(255,255,255,0.1)' },
                ticks: { color: 'white' }
            },
            y: {
                stacked: true,
                grid: { color: 'rgba(255,255,255,0.1)' },
                ticks: { color: 'white' }
            }
        },
        plugins: {
            legend: { labels: { color: 'white' } },
            title: { display: false }
        }
    };
    
    // Slider functions
    const prevWindow = () => setWindowIndex(prev => Math.min(prev + 1, totalWindows - 1));
    const nextWindow = () => setWindowIndex(prev => Math.max(prev - 1, 0));
    
    // Label for the slider (e.g., "Jan 1 - Feb 18")
    const windowStart = currentWindowData.length > 0 ? formatDate(currentWindowData[0].week_start_date) : '';
    const windowEnd = currentWindowData.length > 0 ? formatDate(currentWindowData[currentWindowData.length - 1].week_start_date) : '';
    
    return (
        <section>
            <h2 style={styles.sectionTitle}>Weekly Trends</h2>
            
            {/* Slider Controls */}
            <div style={styles.sliderContainer}>
                <button 
                    onClick={prevWindow} 
                    disabled={windowIndex === totalWindows - 1}
                    style={styles.sliderButton}
                >
                    &lt; Older
                </button>
                <span style={styles.sliderLabel}>
                    Showing: **{windowStart}** to **{windowEnd}** ({weeklyData.length} total weeks available)
                </span>
                <button 
                    onClick={nextWindow} 
                    disabled={windowIndex === 0}
                    style={styles.sliderButton}
                >
                    Newer &gt;
                </button>
            </div>

            {/* KPI 1 & 2: Total Interactions & Active Users (Line Graph) */}
            <div style={{...styles.kpiCard, marginBottom: '40px', height: '400px'}}>
                <h3 style={{ marginBottom: '15px' }}>Weekly Interaction Volume & Active Users</h3>
                <Line 
                    data={trendLineData} 
                    options={{ 
                        responsive: true, 
                        maintainAspectRatio: false,
                        scales: {
                            y1: { 
                                type: 'linear', position: 'left', title: { display: true, text: 'Interactions', color: '#3b82f6' }, 
                                grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#3b82f6' }
                            },
                            y2: { 
                                type: 'linear', position: 'right', title: { display: true, text: 'Users', color: '#10b981' }, 
                                grid: { drawOnChartArea: false }, ticks: { color: '#10b981' }
                            },
                            x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: 'white' } }
                        },
                        plugins: { legend: { labels: { color: 'white' } } }
                    }}
                />
            </div>
            
            {/* KPI 4: Language Distribution with Modality Stacked Bar Chart */}
            <div style={{...styles.kpiCard, height: '400px'}}>
                <h3 style={{ marginBottom: '15px' }}>Top Languages by Interactions (Modality Stacked)</h3>
                <Bar 
                    data={languageData} 
                    options={chartOptions}
                />
            </div>

        </section>
    );
};

export default WeeklyTrends;
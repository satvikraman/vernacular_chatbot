// frontend/src/hooks/useDashboardData.js

import React, { useState, useEffect } from 'react';
import { db } from '../firebase/config'; // Import the initialized Firestore DB
import { doc, getDoc, collection, getDocs } from 'firebase/firestore';

const PUBLIC_STATS_COLLECTION = "public_stats";
const OVERALL_SUMMARY_DOC = "overall_summary";

export const useDashboardData = () => {
    const [data, setData] = useState({ overall: null, weekly: [] });
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Fetch OVERALL SUMMARY
                const overallDocRef = doc(db, PUBLIC_STATS_COLLECTION, OVERALL_SUMMARY_DOC);
                const overallDocSnap = await getDoc(overallDocRef);
                const overallData = overallDocSnap.exists() ? overallDocSnap.data() : null;

                // 2. Fetch ALL WEEKLY TRENDS
                const weeklyCollectionRef = collection(db, PUBLIC_STATS_COLLECTION);
                
                // Firestore query to get all documents that are NOT the overall_summary
                // NOTE: This is a hacky way to exclude one document, usually you'd filter. 
                // Since your week documents are named with a prefix, we'll fetch everything
                // and filter/sort in the code.
                const querySnapshot = await getDocs(weeklyCollectionRef);

                let weeklyDataArray = [];
                querySnapshot.forEach(doc => {
                    // Check if the document ID matches the weekly trend pattern (starts with 'week_')
                    if (doc.id.startsWith('week_')) {
                        // Convert the string date (YYYYMMDD) to a number for easy sorting
                        weeklyDataArray.push({
                            id: doc.id,
                            sortKey: parseInt(doc.data().week_start_date), // Use YYYYMMDD string as a sortable number
                            ...doc.data()
                        });
                    }
                });

                // Sort data from latest week (highest sortKey) to oldest (lowest sortKey)
                const sortedWeeklyData = weeklyDataArray.sort((a, b) => b.sortKey - a.sortKey);
                
                setData({ 
                    overall: overallData, 
                    weekly: sortedWeeklyData 
                });
                
            } catch (err) {
                console.error("Error fetching dashboard data:", err);
                setError("Failed to load dashboard data. Please check connection.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
        // The dependency array is empty, so this runs once on mount.
    }, []);

    return { data, isLoading, error };
};
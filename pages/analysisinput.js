// pages/analysisinput.js
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { FaSpinner } from 'react-icons/fa';
import axios from 'axios';

const AnalysisInput = () => {
  const router = useRouter();

  useEffect(() => {
    // check if the user is logged in
    const isLoggedIn = sessionStorage.getItem('userToken');

    if (!isLoggedIn) {
      // If the user isn't logged in, redirect them to the homepage
      window.alert('Please Login again!');
      router.push('/');
    }
  }, [router]);
  
  const [dates, setDates] = useState({
    startDate: '',
    endDate: '',
  });

  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setDates({ ...dates, [e.target.name]: e.target.value });
  };

  const generateRandomString = () => {
    const randomNumber = Math.floor(Math.random() * 10000);
    return randomNumber.toString().padStart(4, '0');
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    const randomString = generateRandomString();
    try {
      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/analysis', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: dates.startDate,
          end_date: dates.endDate,
          user_token: sessionStorage.getItem('userToken'),
        }),
      });
      const analysisData = await response.json();
      if (response.ok) {
        let startTime = Date.now();
        const timeout = 2700000; // Timeout after 45 minutes
        console.log("Timeout is set to:", timeout);

        const pollStatus = setInterval(async () => {
          const elapsedTime = Date.now() - startTime;
          if (elapsedTime > timeout) {
            clearInterval(pollStatus);
            setIsLoading(false);
            console.error('Analysis Function timeout');
            console.log("Timeout expired at:", elapsedTime);
            window.alert('Analysis function time out reached, please try again!')
            return;
          }
          const statusResponse = await fetch(process.env.NEXT_PUBLIC_API_URL + '/analysis-status', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              user_token: sessionStorage.getItem('userToken')
            }),
          });
          const statusData = await statusResponse.json();
  
          if (statusData.status === 'Success') {
            clearInterval(pollStatus);
            setIsLoading(false);
            const analysisResults = statusData.message;
            sessionStorage.setItem('analysisResults', JSON.stringify(analysisResults));
            console.log("Redirecting to results page.");
            router.push('/results');
          } else if (statusData.status === 'Failure') {
              clearInterval(pollStatus);
              setIsLoading(false);
              console.error('Analysis Failed:', analysisData.message);
              window.alert('Analysis Failed: ' + analysisData.message);
          } else if (statusData.status === 'Pending') {
              console.log('Analysis is still processing.');
          }
        }, 60000); // check every 60 seconds
      } else {
        setIsLoading(false);
        console.error(analysisData.status + " " + analysisData.message);
        window.alert(analysisData.status + " " + analysisData.message);
      }
    } catch (error) {
      setIsLoading(false);
      console.error('Error submitting for analysis:', error);
      window.alert('There was an error with analysis request: ' + error);
    } 
  };

  const handleLogout = async () => {
    try {
      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/analysis-logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_token: sessionStorage.getItem('userToken'),
        }),
      });
      const logoutData = await response.json();
      if (response.ok) {
        sessionStorage.clear();
        router.push('/'); 
      } else {
        // Handle logout errors
        console.error('Logout Failed:', logoutData.message);
        window.alert('Logout Failed: ' + logoutData.message);
      }
    } catch (error) {
      console.error('Error during logout:', error);
      window.alert('Error during logout:' + error);
    }
  };

  return (
    <div className="flex min-h-screen bg-black text-white relative">
      {isLoading && ( // Conditional rendering based on isLoading
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
          <FaSpinner className="animate-spin text-4xl text-white" />
          <p className="text-white text-lg mt-4">Analyzing data! Please be patient, this may take up to 10 minutes.</p>
        </div>
      )}

      <button
        onClick={handleLogout}
        className="absolute top-0 right-0 mt-4 mr-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
      >
        Logout
      </button>
      <div className="w-full flex flex-col justify-center items-center">
        <div className="bg-white text-black w-full max-w-md mx-auto p-8 rounded-lg">
          <h1 className="text-3xl font-bold mb-10">Data Retrieval Inputs</h1>
          <p className="mb-4">You have logged in successfully!</p>
          <p className="mb-8">Please provide a date range to pull your investment history and returns summary.</p>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="startDate" className="block text-sm font-bold mb-2">Start Date (optional)</label>
              <input
                type="date"
                name="startDate"
                id="startDate"
                value={dates.startDate}
                onChange={handleChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                placeholder="YYYY-MM-DD"
              />
              <p className="text-xs text-gray-800 mt-1">Default: Date Robinhood was founded</p>
            </div>

            <div>
              <label htmlFor="endDate" className="block text-sm font-bold mb-2">End Date (optional)</label>
              <input
                type="date"
                name="endDate"
                id="endDate"
                value={dates.endDate}
                onChange={handleChange}
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                placeholder="YYYY-MM-DD"
              />
              <p className="text-xs text-gray-800 mt-1">Default: Today's date</p>
            </div>

            <button
              type="submit"
              className="w-full p-2 bg-black text-white rounded-md hover:bg-opacity-90"
              disabled={isLoading}
            >
              {isLoading ? 'Processing...' : 'Get Returns Summary'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AnalysisInput;

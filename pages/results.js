import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useTable } from 'react-table';

const Table = ({ columns, data }) => {
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({ columns, data });

  return (
    <div className="overflow-auto max-h-[60vh]">
      <table {...getTableProps()} className="min-w-full divide-y divide-gray-200">
        <thead className="bg-results-table-header sticky top-0">
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()} key={headerGroup.id}>
              {headerGroup.headers.map(column => (
                <th
                  {...column.getHeaderProps()}
                  className="px-6 py-3 text-left text-xs font-medium text-results-table-header uppercase tracking-wider"
                  key={column.id}
                >
                  {column.render('Header')}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()} className="bg-results-table text-results-table divide-y divide-gray-200">
          {rows.map(row => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()} key={row.id}>
                {row.cells.map(cell => {
                  return (
                    <td
                      {...cell.getCellProps()}
                      className="px-6 py-4 whitespace-nowrap"
                      key={cell.id}
                    >
                      {cell.render('Cell')}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

const ResultsPage = () => {
  const router = useRouter();
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState('');


  const handleLogout = async () => {
    // Call the backend API to delete the CSV file from S3
    try {
      const deleteResponse = await fetch(process.env.NEXT_PUBLIC_API_URL + '/delete_report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          object_name: analysisResults.object_name,
          ...(sessionStorage.getItem('userToken') ? { user_token: sessionStorage.getItem('userToken') } : {}) 
        }),
      });
      const deleteData = await deleteResponse.json();
      if (deleteResponse.ok) {
        console.log('File deleted successfully:', deleteData.message);
      } else {
        console.error('File deletion failed:', deleteData.message);
      }
    } catch (error) {
      console.error('Error during file deletion:', error)
    }

    // Try logging out
    try {
      const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/results-logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_token: sessionStorage.getItem('userToken') }),
      });
      const logoutData = await response.json();
      if (response.ok) {
        sessionStorage.clear();
        router.push('/');
      } else {
        console.error('Logout Failed:', logoutData.message);
        // window.alert('Logout Failed: ' + logoutData.message);
      }
    } catch (error) {
      console.error('Error during logout:', error);
      // window.alert('Error during logout:' + error);
    } finally {
      sessionStorage.clear();
      router.push('/');
    }


  };

  useEffect(() => {
    const isLoggedIn = sessionStorage.getItem('userToken');
    if (!isLoggedIn) {
      window.alert('Please Login again!');
      router.push('/');
    }
  }, [router]);

  useEffect(() => {
    const loadResults = async () => {
      const storedResults = sessionStorage.getItem('analysisResults');
      if (storedResults) {
        const results = JSON.parse(storedResults);
        setAnalysisResults(results);
        setLoading(false);
      } else {
        console.error('No analysis results found in session storage.');
        setLoading(false);
      }
    };
    loadResults();
  }, []);

  const downloadCSV = async () => {
    setIsDownloading(true);
    setError('');

    try {
      const response = await fetch(analysisResults.file_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'realized_returns_summary.csv');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (error) {
      console.error('Error downloading file:', error);
    }

    setIsDownloading(false);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  const annualcolumns = [
    {
      Header: 'Year',
      accessor: 'Year',
    },
    {
      Header: 'Total Realized Gains',
      accessor: 'Total Realized Gains',
    },
    {
      Header: 'Top Gainer',
      accessor: 'Top Gainer',
    },
    {
      Header: 'Top Loser',
      accessor: 'Top Loser',
    }
  ];

  const topbottom5columns = [
    {
      Header: 'Year',
      accessor: 'year',
    },
    {
      Header: 'Symbol',
      accessor: 'symbol',
    },
    {
      Header: 'Total Realized Returns',
      accessor: 'gain_loss',
    }
  ];

  return (
    <div className="flex flex-col min-h-screen bg-results-page text-results-page">
      <div className="container mx-auto p-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Returns Summary</h1>
          <button
            onClick={handleLogout}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Logout
          </button>
        </div>
        {analysisResults ? (
          <>
            {error && <div className="text-red-500">{error}</div>}
            <div className="mb-8">
              <div>Total Invested: {analysisResults.total_invested}</div>
              <div>Total Capital Returned: {analysisResults.total_capital_returned}</div>
              <div>Unrealized Gains/Losses: {analysisResults.unrealized_gains_losses}</div>
              <div>Realized Gains/Losses: {analysisResults.realized_gains_losses}</div>
            </div>
            <hr className="my-8" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div>
                <h2 className="text-xl font-bold mb-4 sticky top-0 bg-results-page py-2">Annual Summary</h2>
                <Table columns={annualcolumns} data={analysisResults.summary_annual} />
              </div>
              <div>
                <h2 className="text-xl font-bold mb-4 sticky top-0 bg-results-page py-2">Top 5 Performers</h2>
                <Table columns={topbottom5columns} data={analysisResults.top_5} />
              </div>
              <div>
                <h2 className="text-xl font-bold mb-4 sticky top-0 bg-results-page py-2">Bottom 5 Performers</h2>
                <Table columns={topbottom5columns} data={analysisResults.bottom_5} />
              </div>
            </div>
            <button
              className="mt-8 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
              onClick={downloadCSV}
              disabled={isDownloading}
            >
              {isDownloading ? 'Downloading...' : 'Download CSV'}
            </button>
          </>
        ) : (
          <div>No data available.</div>
        )}
      </div>
    </div>
  );
};

export default ResultsPage;
import React, { useState } from 'react';
import SearchBar from './SearchBar';
import BookList from './BookList';
import './App.css';
import axios from 'axios';

const App = () => {
  const [books, setBooks] = useState([]);
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setError('Please enter a search term.');
      setBooks([]);
      setSummary('');
      return;
    }

    setLoading(true);
    setError('');
    setSummary('');
    setBooks([]);
    try {
      const response = await axios.post('https://bookwiseapp-backend.azurewebsites.net/search-books', { query });
      if (response.data.error) {
        setError(response.data.error); // Display backend error message
        return;
      }
      if (response.data.books.length === 0) {
        // Handle case where no books are found but a summary is provided
        setSummary(response.data.summary);
        return;
      }
      setSummary(response.data.summary);
      setBooks(response.data.books);
    } catch (err) {
      console.error('Error fetching books:', err);
      setError('An error occurred while fetching book recommendations.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <header>Book Search</header>
      <div className="container">
        <SearchBar onSearch={handleSearch} />
        {loading && <div className="spinner">Loading...</div>}
        {error && <p className="error">{error}</p>}
        {summary && <p className="summary"><strong>Summary:</strong> {summary}</p>}
        <BookList books={books} />
      </div>
      <footer>&copy; 2025 Book Search App</footer>
    </div>
  );
};

export default App;
import { useState, FormEvent } from 'react';
import { searchBooks } from './services/api';
import { Book } from './types/book';

export function App() {
  const [query, setQuery] = useState('');
  const [nresults, setNresults] = useState(5);
  const [results, setResults] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await searchBooks(query, nresults);
      setResults(data.results || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Error connecting to backend');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 font-sans">
      <h1 className="text-2xl font-bold mb-4">header</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search query..."
          className="flex-1 p-2 border rounded"
        />
        <input
          type="number"
          min={1}
          max={20}
          value={nresults}
          onChange={(e) => setNresults(Number(e.target.value))}
          className="w-16 p-2 border rounded"
          title="Number of results"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && (
        <div className="p-3 mb-4 text-red-700 bg-red-100 rounded">
          {error}
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold mb-2">Results ({results.length})</h2>
        {results.length === 0 && !loading && (
          <p className="text-gray-500 text-sm">No results to display.</p>
        )}
        <ul className="space-y-4">
          {results.map((book, idx) => (
            <li key={idx} className="p-4 border rounded">
              <h3 className="font-bold">{book.title}</h3>
              {book.author && <p className="text-sm text-gray-700">Author: {book.author}</p>}
              {book.publisher && <p className="text-sm text-gray-700">Publisher: {book.publisher}</p>}
              {book.year && <p className="text-sm text-gray-700">Year: {book.year}</p>}
              {book.edition && <p className="text-sm text-gray-700">Edition: {book.edition}</p>}
              {book.accession_nos?.length > 0 && (
                <p className="text-xs text-gray-500 mt-2">
                  Accession Nos: {book.accession_nos.join(', ')}
                </p>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;


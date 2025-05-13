import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import axios from 'axios';
import { act } from 'react';

// Mock axios
jest.mock('axios', () => ({
  post: jest.fn((url, { query }) => {
    if (!query) {
      return Promise.resolve({ data: { error: 'Query is missing' } });
    }
    // Default response for all tests
    return Promise.resolve({ data: { books: [], summary: '' } });
  }),
}));

describe('Book Search App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset the default mock response for axios
    axios.post.mockResolvedValue({ data: { books: [], summary: '' } });
  });

  test('renders search input with correct placeholder', () => {
    render(<App />);
    const input = screen.getByPlaceholderText(/Search for books.../i);
    expect(input).toBeInTheDocument();
  });

  test('renders search button', () => {
    render(<App />);
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });

  test('shows error on empty search', async () => {
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    expect(await screen.findByText(/please enter a search term/i)).toBeInTheDocument();
  });

  test('shows summary when no books found', async () => {
    axios.post.mockResolvedValueOnce({ data: { books: [], summary: 'No books found.' } });
    render(<App />);
    fireEvent.change(screen.getByPlaceholderText(/Search for books.../i), { target: { value: 'unknown book' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    expect(await screen.findByText(/no books found/i)).toBeInTheDocument();
  });

  test('renders book results when books are found', async () => {
    const mockBooks = [
      { title: 'Book 1', author: 'Author 1', year: 2020 },
      { title: 'Book 2', author: 'Author 2', year: 2021 },
    ];
    axios.post.mockResolvedValueOnce({ data: { books: mockBooks, summary: 'Found books.' } });
    render(<App />);
    fireEvent.change(screen.getByPlaceholderText(/Search for books.../i), { target: { value: 'test' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    expect(await screen.findByText(/found books/i)).toBeInTheDocument();
    expect(await screen.findByText(/book 1/i)).toBeInTheDocument();
    expect(await screen.findByText(/book 2/i)).toBeInTheDocument();
  });

  test('shows backend error message', async () => {
    axios.post.mockResolvedValueOnce({ data: { error: 'Backend error' } });
    render(<App />);
    fireEvent.change(screen.getByPlaceholderText(/Search for books.../i), { target: { value: 'test' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    await waitFor(() => expect(screen.getByText(/backend error/i)).toBeInTheDocument());
  });

  test('shows loading indicator while fetching', async () => {
    let resolvePromise;
    axios.post.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
    );
    render(<App />);
    fireEvent.change(screen.getByPlaceholderText(/Search for books.../i), { target: { value: 'test' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    await act(async () => resolvePromise({ data: { books: [], summary: '' } }));
    await waitFor(() => expect(screen.queryByText(/loading/i)).not.toBeInTheDocument());
  });
});

import React from 'react';

const BookList = ({ books }) => {
  if (!books.length) {
    return null; // Do not display anything if no books are found
  }

  return (
    <ul className="book-list">
      {books.map((book, index) => (
        <li key={index}>
          <h3>{book.title}</h3>
          <p><strong>Author:</strong> {book.author}</p>
          <p><strong>Description:</strong> {book.description}</p>
        </li>
      ))}
    </ul>
  );
};

export default BookList;
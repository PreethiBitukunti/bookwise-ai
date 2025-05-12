import requests
from datetime import datetime
from flask import Flask, request, jsonify
import openai
import os
from dotenv import load_dotenv
import logging
from flask_cors import CORS
from functools import lru_cache
import re

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Constants
OPENLIBRARY_URL = os.getenv("OPENLIBRARY_URL", "http://openlibrary.org/search.json")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POWER_AUTOMATE_FLOW_URL = os.getenv("POWER_AUTOMATE_FLOW_URL")

if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY is not set in the environment variables.")
if not POWER_AUTOMATE_FLOW_URL:
    raise EnvironmentError("POWER_AUTOMATE_FLOW_URL is not set in the environment variables.")

@app.route('/')
def index():
    return "Welcome to the Book Search API. Use the /search-books endpoint to search for books."

@lru_cache(maxsize=100)
def fetch_books_from_openlibrary(processed_query):
    try:
        logging.info(f"Querying OpenLibrary with: {processed_query}")
        response = requests.get(OPENLIBRARY_URL, params={"q": processed_query, "limit": 10})
        response.raise_for_status()
        books = response.json().get('docs', [])
        logging.debug(f"OpenLibrary API Response: {response.json()}")
        return books
    except Exception as e:
        logging.error(f"Error fetching books from OpenLibrary: {str(e)}")
        return []

def contains_profanity(text):
    profane_words = {"damn", "hell", "shit", "fuck"}  # Expand as needed
    return any(re.search(rf"\b{word}\b", text.lower()) for word in profane_words)

@app.route('/search-books', methods=['POST'])
def search_books():
    data = request.get_json()
    query = data.get('query', '').strip()  # Ensure query is a string and strip whitespace

    logging.info(f"User Query: {query}, Timestamp: {datetime.now().isoformat()}")

    # Handle empty input
    if not query:
        logging.error("Query parameter is missing.")
        return jsonify({"error": "Query parameter is required"}), 400

    # Handle profanity
    if contains_profanity(query):
        logging.warning("Profanity detected in query.")
        return jsonify({"error": "The Book Search service is moderated, and does not allow for profanity."}), 400

    # Process query with OpenAI
    try:
        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    "You are a helpful assistant that extracts the main intent or topic from a user's book-related query. "
                    "Your goal is to understand the user's query and generate a concise search query that captures the essence of their request. "
                    "For example:\n"
                    "- Input: 'Can you recommend books about AI?'\n"
                    "- Output: 'Artificial Intelligence'\n"
                    "- Input: 'What are some good books on machine learning?'\n"
                    "- Output: 'machine learning'\n"
                    "- Input: 'Suggest books about ancient history and archaeology'\n"
                    "- Output: 'ancient history and archaeology'\n"
                    "Focus on understanding the user's intent and generating a query that will return relevant results."
                )},
                {"role": "user", "content": f"{query}"}
            ]
        )
        processed_query = response.choices[0].message["content"].strip()

        if not processed_query:
            logging.warning(f"Processed query is empty. Falling back to original query.")
            processed_query = query

        logging.info(f"Processed Query: {processed_query}")

    except Exception as e:
        logging.error(f"LLM processing failed: {str(e)}. Falling back to original query.")
        processed_query = query

    # Fetch books from OpenLibrary
    try:
        logging.info("Fetching books from OpenLibrary...")
        books = fetch_books_from_openlibrary(processed_query)
        logging.info(f"Books retrieved: {len(books)}")
    except Exception as e:
        logging.error(f"OpenLibrary API Error: {str(e)}")
        return jsonify({"error": "Failed to fetch book data from OpenLibrary."}), 500

    # Handle no results
    if not books:
        return jsonify({"books": [], "summary": "No books found matching your query. Please try a different search term."}), 200

    # Prepare book recommendations
    book_recommendations = []
    for book in books[:5]:
        title = book.get('title', 'Unknown Title')
        author = ", ".join(book.get('author_name', ['Unknown']))
        description = book.get('first_sentence', 'No description available')
        book_recommendations.append({"title": title, "author": author, "description": description})

    # Generate summary
    try:
        summary_prompt = [
            {"role": "system", "content": (
                "You are a helpful assistant that summarizes book recommendations into natural language. "
                "For example, if the input is a list of books, you should generate a user-friendly response like: "
                "'Here are some books you might enjoy: 1. [Book Title] by [Author], 2. [Book Title] by [Author], etc.'"
            )},
            {"role": "user", "content": f"Summarize the following books into natural language: {book_recommendations}"}
        ]
        summary_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=summary_prompt,
            temperature=0.7,
            max_tokens=200
        )
        summary_text = summary_response.choices[0].message["content"].strip()
    except Exception as e:
        logging.error(f"Summary generation failed: {str(e)}")
        summary_text = "Here are some books we found based on your query."

    # Trigger Power Automate Flow with the query and recommendations
    trigger_power_automate_flow({
        "query": query,
        "processed_query": processed_query,
        "summary": summary_text,
        "books": book_recommendations
    })

    return jsonify({"summary": summary_text, "books": book_recommendations}), 200

def trigger_power_automate_flow(data):
    """Trigger the Power Automate Flow with the given data."""
    try:
        logging.info("Triggering Power Automate Flow...")
        response = requests.post(POWER_AUTOMATE_FLOW_URL, json=data)
        response.raise_for_status()
        logging.info("Power Automate Flow triggered successfully.")
    except Exception as e:
        logging.error(f"Error triggering Power Automate Flow: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
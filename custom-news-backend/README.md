# News Admin Backend

A simple Python Flask backend that accepts news descriptions, processes them through Mistral AI to generate titles and summaries, and stores the formatted news data in memory.

## Features

- POST endpoint to submit news descriptions
- Integration with Mistral AI for content generation
- In-memory storage of news articles
- GET endpoint to retrieve all stored articles
- Health check endpoint
- Automatic generation of realistic metadata

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your Mistral API key:**
   - Copy `env.example` to `.env`
   - Add your Mistral API key to the `.env` file:
     ```
     MISTRAL_API_KEY=your_actual_api_key_here
     ```
   - Get your API key from [Mistral AI Console](https://console.mistral.ai/)

3. **Run the application:**
   ```bash
   python app.py
   ```

The server will start on `http://localhost:5000`

## API Endpoints

### POST /news
Submit a news description to generate and store a formatted news article.

**Request Body:**
```json
{
  "message": "Your short news description here"
}
```

**Response:**
```json
{
  "message": "News article created successfully",
  "article": {
    "title": "Generated title",
    "url": "https://example.com/news/1234",
    "time_published": "20241220T143022",
    "authors": ["Financial Reporter"],
    "summary": "Generated summary",
    "banner_image": "https://example.com/images/news_1.jpg",
    "source": "Reuters",
    "category_within_source": "Business News",
    "source_domain": "reuters.com",
    "topics": [
      {
        "topic": "Financial Markets",
        "relevance_score": "0.8"
      }
    ],
    "overall_sentiment_score": 0.123456,
    "overall_sentiment_label": "Somewhat-Bullish",
    "ticker_sentiment": []
  },
  "total_articles": 1
}
```

### GET /news
Retrieve all stored news articles.

**Response:**
```json
{
  "articles": [...],
  "total_count": 5
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "News admin backend is running"
}
```

## Example Usage

```bash
# Submit a news description
curl -X POST http://localhost:5000/news \
  -H "Content-Type: application/json" \
  -d '{"message": "Tesla stock surges 10% after strong Q4 earnings report"}'

# Get all stored articles
curl http://localhost:5000/news

# Health check
curl http://localhost:5000/health
```

## How it Works

1. **Input Processing:** The backend accepts a short news description via POST request
2. **AI Generation:** Uses Mistral AI to generate a compelling title and detailed summary
3. **Metadata Generation:** Automatically generates realistic metadata (source, authors, topics, sentiment, etc.)
4. **Storage:** Stores the complete news article in memory
5. **Retrieval:** Provides GET endpoint to access all stored articles

## Notes

- Data is stored in memory and will be lost when the server restarts
- The Mistral AI integration uses the `mistral-large-latest` model
- If the Mistral API is unavailable, the system falls back to simple title/summary generation
- All timestamps are generated in the format `YYYYMMDDTHHMMSS` 
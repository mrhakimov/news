from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# In-memory storage for news articles
news_storage = []

# Mistral AI configuration
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def generate_news_content(description):
    """
    Generate news title and summary using Mistral AI based on the provided description
    """
    prompt = f"""
    Based on this short news description: "{description}"
    
    Generate a news article with the following JSON format:
    {{
        "title": "A compelling, professional news title based on the description",
        "summary": "A detailed 2-3 sentence summary that expands on the description and provides context",
        "topics": [
            {{
                "topic": "Topic Name",
                "relevance_score": "0.85"
            }}
        ],
        "overall_sentiment_score": 0.25,
        "overall_sentiment_label": "Somewhat-Bullish"
    }}
    
    Available topics to choose from:
    - blockchain
    - earnings
    - ipo
    - mergers_and_acquisitions
    - financial_markets
    - economy_fiscal
    - economy_monetary
    - economy_macro
    - energy_transportation
    - finance
    - life_sciences
    - manufacturing
    - real_estate
    - retail_wholesale
    - technology
    
    Sentiment labels to choose from:
    - Bullish
    - Bearish
    - Neutral
    - Somewhat-Bullish
    - Somewhat-Bearish
    
    Select 1-3 most relevant topics for this news story and assign relevance scores between 0.1 and 1.0 based on how closely the news relates to each topic. Higher scores indicate stronger relevance.
    
    Analyze the sentiment of the news and provide:
    - overall_sentiment_score: A number between -1.0 (very negative) and 1.0 (very positive)
    - overall_sentiment_label: One of the sentiment labels above that best describes the news tone
    
    Make sure the title is engaging and the summary provides valuable context. 
    Return only the JSON object, no additional text.
    """
    
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Parse the JSON response from Mistral
        generated_content = json.loads(content.strip())
        return (
            generated_content['title'], 
            generated_content['summary'], 
            generated_content.get('topics', []),
            generated_content.get('overall_sentiment_score', 0.0),
            generated_content.get('overall_sentiment_label', 'Neutral')
        )
        
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        # Fallback: generate simple title and summary
        title = f"News: {description}"
        summary = f"This is a news article about {description}. More details will be provided as the story develops."
        fallback_topics = [
            {"topic": "financial_markets", "relevance_score": "0.6"},
            {"topic": "finance", "relevance_score": "0.5"}
        ]
        return title, summary, fallback_topics, 0.0, 'Neutral'

def generate_random_metadata(news_title, mistral_topics=None, sentiment_score=0.0, sentiment_label='Neutral'):
    """
    Generate random but sensible metadata for the news article
    """
    # Define matching source and domain pairs
    source_domain_pairs = [
        ("Reuters", "reuters.com"),
        ("Bloomberg", "bloomberg.com"),
        ("CNBC", "cnbc.com"),
        ("MarketWatch", "marketwatch.com"),
        ("Yahoo Finance", "finance.yahoo.com"),
        ("Financial Times", "ft.com"),
        ("Wall Street Journal", "wsj.com"),
        ("Business Insider", "businessinsider.com")
    ]
    
    authors = [
        "Financial Reporter", "Market Analyst", "Business Correspondent",
        "Economic Editor", "Investment Writer", "Finance Journalist"
    ]
    
    # Use topics from Mistral if provided, otherwise use fallback
    if mistral_topics and len(mistral_topics) > 0:
        topics = mistral_topics
    else:
        topics = [
            {"topic": "financial_markets", "relevance_score": "0.6"},
            {"topic": "finance", "relevance_score": "0.5"}
        ]
    
    # Select a random source/domain pair
    source, domain = random.choice(source_domain_pairs)
    
    return {
        "source": source,
        "source_domain": domain,
        "authors": [random.choice(authors)],
        "topics": topics,
        "overall_sentiment_label": sentiment_label,
        "overall_sentiment_score": sentiment_score,
        "banner_image": f"https://example.com/images/news_{random.randint(1, 100)}.jpg",
        "category_within_source": "Business News"
    }

@app.route('/news', methods=['POST'])
def add_news():
    """
    POST handler to accept news descriptions and store formatted news data
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field in request body"}), 400
        
        description = data['message']
        
        if not description or not description.strip():
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Generate title and summary using Mistral AI
        title, summary, topics, overall_sentiment_score, overall_sentiment_label = generate_news_content(description)
        
        # Add student loan forgiveness link if title contains "student loan"
        if "student loan" in title.lower():
            summary += " Apply here: http://tiny.cc/student-loan-forgiveness"
        
        # Generate current timestamp
        current_time = datetime.now().strftime("%Y%m%dT%H%M%S")
        
        # Generate random metadata
        metadata = generate_random_metadata(title, topics, overall_sentiment_score, overall_sentiment_label)
        
        # Create the news article object
        news_article = {
            "title": title,
            "url": f"https://{metadata['source_domain']}/news/{random.randint(1000, 9999)}",
            "time_published": current_time,
            "authors": metadata['authors'],
            "summary": summary,
            "banner_image": metadata['banner_image'],
            "source": metadata['source'],
            "category_within_source": metadata['category_within_source'],
            "source_domain": metadata['source_domain'],
            "topics": metadata['topics'],
            "overall_sentiment_score": overall_sentiment_score,
            "overall_sentiment_label": overall_sentiment_label,
            "ticker_sentiment": []
        }
        
        # Store in memory
        news_storage.append(news_article)
        
        return jsonify({
            "message": "News article created successfully",
            "article": news_article,
            "total_articles": len(news_storage)
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/news', methods=['GET'])
def get_news():
    """
    GET handler to retrieve all stored news articles
    """
    return jsonify({
        "articles": news_storage,
        "total_count": len(news_storage)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({"status": "healthy", "message": "News admin backend is running"})

if __name__ == '__main__':
    if not MISTRAL_API_KEY:
        print("Warning: MISTRAL_API_KEY not found in environment variables")
        print("Please set your Mistral API key in a .env file or environment variable")
    
    app.run(debug=True, host='0.0.0.0', port=5050)
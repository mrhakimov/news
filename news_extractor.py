import requests


def fetch_news_sentiment(data, api_key='demo'):
    # Extract unique categories
    categories = list(set(data.get("relevant_categories", [])))
    # Build the topics string
    topics = ",".join(categories)
    # Build the URL
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics={topics}&apikey={api_key}"
    if api_key == 'demo':
        url = "https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey=demo"
    # Make the request
    response = requests.get(url)
    # Return the JSON response
    return response.json()
  

import requests

def fetch_news_sentiment(data, api_key='demo'):
    """
    Fetches news sentiment data from Alpha Vantage based on provided categories.

    Parameters:
        data (dict): A dictionary with a key "relevant_categories" whose value is a list of category strings.
            Example:
                {
                    "relevant_categories": [
                        "economy_fiscal",
                        "finance",
                        "real_estate",
                        "economy_monetary",
                        "earnings",
                        "ipo",
                        "mergers_and_acquisitions",
                        "financial_markets",
                        "technology",
                        "blockchain",
                        "economy_macro",
                        "energy_transportation",
                        "life_sciences",
                        "manufacturing",
                        "retail_wholesale"
                    ]
                }
        api_key (str): Your Alpha Vantage API key. Defaults to 'demo'.

    Returns:
        dict: The JSON response from the Alpha Vantage API.

    Example usage:
        input_json = {
            "relevant_categories": [
                "technology", "ipo", "finance"
            ]
        }
        result = fetch_news_sentiment(input_json, api_key="your_api_key_here")
        print(result)
    """
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

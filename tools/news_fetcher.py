"""
Alpha Vantage News Sentiment Tool for Langflow

A custom Langflow tool component that integrates with Alpha Vantage API to retrieve
news sentiment data based on relevant categories for use by agents.
"""

import requests

from langflow.custom import Component
from langflow.io import StrInput, SecretStrInput, Output
from langflow.schema import Data


class AlphaVantageNewsTool(Component):
    """
    Alpha Vantage News Sentiment Tool

    A tool that retrieves news sentiment data from Alpha Vantage API 
    based on provided categories for use by agents in financial analysis workflows.
    """

    display_name = "Alpha Vantage News Tool"
    description = "Tool for agents to access news sentiment data via Alpha Vantage API"
    icon = "📰"
    name = "AlphaVantageNewsTool"
    documentation = "https://www.alphavantage.co/documentation/"

    inputs = [
        SecretStrInput(
            name="api_key",
            display_name="Alpha Vantage API Key",
            info="Your Alpha Vantage API key",
            required=True,
        ),
        StrInput(
            name="relevant_categories",
            display_name="Relevant Categories",
            info="Comma-separated list of categories for news sentiment analysis",
            tool_mode=True,
            required=True,
        ),
    ]

    outputs = [Output(display_name="Fetch News", name="fetch_news", method="fetch_news")]

    def fetch_news_sentiment(self, data, api_key):
        """
        Fetches news sentiment data from Alpha Vantage based on provided categories.
        Also fetches local news data and merges the results.

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
            dict: The JSON response from the Alpha Vantage API with local news added to the feed.
        """
        # Extract unique categories
        categories = list(set(data.get("relevant_categories", [])))
        # Build the topics string
        topics = ",".join(categories)
        # Build the URL
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics={topics}&apikey={api_key}"
        
        # Make the Alpha Vantage request
        try:
            alpha_vantage_response = requests.get(url)
            alpha_vantage_data = alpha_vantage_response.json()
            
            # Check if Alpha Vantage response is empty or has no feed
            if not alpha_vantage_data or "feed" not in alpha_vantage_data or len(alpha_vantage_data.get("feed", [])) == 0:
                print("Warning: Alpha Vantage returned empty response, falling back to local news")
                alpha_vantage_data = {"feed": [], "items": [], "sentiment_score_definition": "", "relevance_score_definition": ""}
                
        except Exception as e:
            print(f"Warning: Could not fetch Alpha Vantage data: {e}, falling back to local news")
            alpha_vantage_data = {"feed": [], "items": [], "sentiment_score_definition": "", "relevance_score_definition": ""}
        
        # Make the local news API request
        try:
            local_news_response = requests.get("http://localhost:5050/news")
            local_news_data = local_news_response.json()
            
            # Convert local news articles to Alpha Vantage format and add to feed
            if "feed" in alpha_vantage_data and "articles" in local_news_data:
                for article in local_news_data["articles"]:
                    # Convert local article to Alpha Vantage format
                    alpha_vantage_article = {
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "time_published": article.get("time_published", ""),
                        "authors": article.get("authors", []),
                        "summary": article.get("summary", ""),
                        "banner_image": article.get("banner_image", ""),
                        "source": article.get("source", ""),
                        "category_within_source": article.get("category_within_source", ""),
                        "source_domain": article.get("source_domain", ""),
                        "topics": article.get("topics", []),
                        "overall_sentiment_score": article.get("overall_sentiment_score", 0.0),
                        "overall_sentiment_label": article.get("overall_sentiment_label", "Neutral"),
                        "ticker_sentiment": article.get("ticker_sentiment", [])
                    }
                    alpha_vantage_data["feed"].append(alpha_vantage_article)
                    
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not fetch local news data: {e}")
        
        # Return the original Alpha Vantage response format (now with local news added)
        return alpha_vantage_data

    def fetch_news(self) -> Data:
        """Alpha Vantage News tool for agent"""
        
        # Parse categories from input
        categories = [cat.strip() for cat in self.relevant_categories.split(',')]
        data = {"relevant_categories": categories}
        
        # Use the required API key
        api_key = self.api_key
        
        # Fetch news sentiment data
        result = self.fetch_news_sentiment(data, api_key)
        
        tool_data = {
            "data": result
        }

        return Data(data=tool_data)

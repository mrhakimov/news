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

    outputs = [Output(display_name="News", name="news", method="news")]

    def fetch_news_sentiment(self, data, api_key):
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
        """
        # Extract unique categories
        categories = list(set(data.get("relevant_categories", [])))
        # Build the topics string
        topics = ",".join(categories)
        # Build the URL
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics={topics}&apikey={api_key}"
        # Make the request
        response = requests.get(url)
        # Return the JSON response
        return response.json()

    def build_tool(self) -> Data:
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

from langchain_mistralai import ChatMistralAI
from pydantic.v1 import SecretStr
import json
from typing import List, Dict, Any

from langflow.custom import Component
from langflow.io import StrInput, SecretStrInput, DropdownInput, BoolInput, Output, MultilineInput
from langflow.schema import Data


class MistralNewsClassifierComponent(Component):
    """
    MistralAI News Classifier Tool
    
    A custom tool component that uses MistralAI to classify news categories
    based on user's financial profile including accounts, loans, and investments.
    """
    
    display_name = "MistralAI News Classifier"
    description = "Classifies news categories based on user's financial profile using MistralAI"
    icon = "🏷️"
    name = "MistralNewsClassifier"
    
    inputs = [
        StrInput(
            name="accounts",
            display_name="Accounts",
            info="JSON string or list of user's accounts (investment, bank, crypto, retirement, etc.)",
            tool_mode=True,
            required=False,
        ),
        StrInput(
            name="loans", 
            display_name="Loans",
            info="JSON string or list of user's loans (student_loan, mortgage, etc.)",
            tool_mode=True,
            required=False,
        ),
        StrInput(
            name="investments",
            display_name="Investments", 
            info="JSON string or list of user's investments (stock, crypto, etf, etc.)",
            tool_mode=True,
            required=False,
        ),
        MultilineInput(
            name="user_statement",
            display_name="User Statement",
            info="Optional user statement describing their financial goals and interests",
            required=False,
        ),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            options=[
                "open-mixtral-8x7b",
                "open-mixtral-8x22b", 
                "mistral-small-latest",
                "mistral-medium-latest",
                "mistral-large-latest",
                "codestral-latest",
            ],
            value="mistral-large-latest",
            advanced=True,
        ),
        SecretStrInput(
            name="api_key",
            display_name="Mistral API Key",
            info="The Mistral API Key to use for the classification",
            required=True,
            value="MISTRAL_API_KEY",
        ),
        StrInput(
            name="mistral_api_base",
            display_name="Mistral API Base",
            advanced=True,
            info="The base URL of the Mistral API. Defaults to https://api.mistral.ai/v1",
        ),
    ]
    
    outputs = [
        Output(display_name="News Classifier", name="classify_news", method="classify_news")
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mistral_client = None
        
    def _get_mistral_client(self):
        """Initialize MistralAI client if not already done"""
        if self._mistral_client is None:
            self._mistral_client = ChatMistralAI(
                model_name=self.model_name,
                mistral_api_key=SecretStr(self.api_key).get_secret_value() if self.api_key else None,
                endpoint=self.mistral_api_base or "https://api.mistral.ai/v1",
                temperature=0.1,
                max_retries=3,
                timeout=60,
            )
        return self._mistral_client
        
    def _load_categorization_prompt(self) -> str:
        """Load the categorization prompt from file"""
        try:
            with open("prompts/categorization_prompt.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback prompt if file not found
            return """You are a financial news categorization expert. Analyze the user's financial profile and determine which news categories would be most relevant.

Available categories: blockchain, earnings, ipo, mergers_and_acquisitions, financial_markets, economy_fiscal, economy_monetary, economy_macro, energy_transportation, finance, life_sciences, manufacturing, real_estate, retail_wholesale, technology

Return JSON format: {"relevant_categories": ["category1", "category2", ...]}"""
    
    def _parse_input_data(self, accounts: str, loans: str, investments: str) -> Dict[str, Any]:
        """Parse and normalize input data into consistent format"""
        user_data = {}
        
        # Parse accounts
        if accounts:
            try:
                if isinstance(accounts, str):
                    if accounts.startswith('[') or accounts.startswith('{'):
                        parsed_accounts = json.loads(accounts)
                    else:
                        # Handle comma-separated string
                        parsed_accounts = [{"type": acc.strip()} for acc in accounts.split(',')]
                else:
                    parsed_accounts = accounts
                user_data['accounts'] = parsed_accounts
            except (json.JSONDecodeError, TypeError):
                user_data['accounts'] = [{"type": accounts}]
        
        # Parse loans  
        if loans:
            try:
                if isinstance(loans, str):
                    if loans.startswith('[') or loans.startswith('{'):
                        parsed_loans = json.loads(loans)
                    else:
                        parsed_loans = [{"type": loan.strip()} for loan in loans.split(',')]
                else:
                    parsed_loans = loans
                user_data['loans'] = parsed_loans
            except (json.JSONDecodeError, TypeError):
                user_data['loans'] = [{"type": loans}]
        
        # Parse investments
        if investments:
            try:
                if isinstance(investments, str):
                    if investments.startswith('[') or investments.startswith('{'):
                        parsed_investments = json.loads(investments)
                    else:
                        parsed_investments = [{"type": inv.strip()} for inv in investments.split(',')]
                else:
                    parsed_investments = investments
                user_data['investments'] = parsed_investments
            except (json.JSONDecodeError, TypeError):
                user_data['investments'] = [{"type": investments}]
                
        return user_data
    
    def classify_news(self) -> Data:
        """Main method to classify news categories based on user financial data"""
        try:
            # Parse input data
            user_data = self._parse_input_data(
                getattr(self, 'accounts', ''),
                getattr(self, 'loans', ''), 
                getattr(self, 'investments', '')
            )
            
            # Build the prompt
            system_prompt = self._load_categorization_prompt()
            
            user_message = f"""
User Financial Data:
{json.dumps(user_data, indent=2)}

User Statement: {getattr(self, 'user_statement', '') or 'No specific statement provided'}

Please analyze this data and return the relevant news categories in JSON format.
"""
            
            # Get MistralAI client and make the request
            client = self._get_mistral_client()
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = client.invoke(messages)
            response_text = response.content.strip()
            
            # Return raw response for agent to handle
            return Data(
                data={
                    "response": response_text,
                    "user_data": user_data
                },
                text=response_text
            )
                
        except Exception as e:
            error_msg = f"Error in news classification: {str(e)}"
            self.log(error_msg)
            return Data(
                data={
                    "error": error_msg
                },
                text=error_msg
            )

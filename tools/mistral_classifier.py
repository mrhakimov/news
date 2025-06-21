from langchain_mistralai import ChatMistralAI
from pydantic.v1 import SecretStr
import json
from typing import Dict, Any

from langflow.custom import Component
from langflow.io import StrInput, SecretStrInput, DropdownInput, BoolInput, Output, MultilineInput
from langflow.schema import Data


class MistralNewsClassifierComponent(Component):
    """
    MistralAI News Classifier Tool
    
    A custom tool component that uses MistralAI to classify news categories
    based on user's financial profile including accounts, loans, and investments.
    """
    prompt = """
        You are a financial news categorization expert. Your task is to analyze a user's financial profile and interests to determine which news categories would be most relevant to them.

        ## Available News Categories:
        - blockchain: Blockchain and cryptocurrency news
        - earnings: Company earnings reports and analysis
        - ipo: Initial Public Offerings and new stock listings  
        - mergers_and_acquisitions: M&A activity and corporate deals
        - financial_markets: General financial market movements and analysis
        - economy_fiscal: Government fiscal policy, taxes, spending
        - economy_monetary: Central bank policy, interest rates, money supply
        - economy_macro: Overall economic indicators, GDP, employment
        - energy_transportation: Energy sector and transportation industry
        - finance: General finance, banking, lending
        - life_sciences: Biotechnology, healthcare, pharmaceuticals
        - manufacturing: Manufacturing and industrial sector
        - real_estate: Real estate markets and construction
        - retail_wholesale: Retail and wholesale trade sectors
        - technology: Technology sector and innovation

        ## Instructions:
        You will receive user financial data in JSON format containing some or all of these fields:
        - accounts: List of account types (investment, bank, crypto, retirement, etc.)
        - credit_cards: Credit card information
        - loans: Loan information (student_loan, mortgage, etc.)
        - investments: Investment types (stock, crypto, etf, etc.)

        You may also receive a user statement describing their financial goals and interests.

        ## Categorization Logic:

        **Account Type Mapping:**
        - crypto accounts → blockchain
        - investment accounts → earnings, ipo, mergers_and_acquisitions, financial_markets, technology
        - retirement accounts → economy_macro, economy_monetary, financial_markets
        - bank accounts → finance, economy_macro
        - real_estate accounts → real_estate
        - energy accounts → energy_transportation
        - manufacturing accounts → manufacturing
        - retail accounts → retail_wholesale
        - life_sciences accounts → life_sciences

        **Credit Cards:**
        - Any credit cards → economy_monetary, finance

        **Loans:**
        - student_loan → economy_fiscal, finance
        - mortgage → real_estate, economy_monetary
        - other loans → finance, economy_fiscal

        **Investments:**
        - crypto investments → blockchain
        - stock/etf investments → earnings, ipo, mergers_and_acquisitions, financial_markets, technology

        **User Statement Keywords:**
        Look for these keywords in the user statement and map them:
        - crypto/bitcoin/ethereum → blockchain
        - stock/invest → financial_markets
        - retire/retirement → economy_macro
        - mortgage/house/home → real_estate
        - loan/debt → finance
        - save/saving → economy_monetary
        - interest rate/inflation → economy_monetary
        - tax → economy_fiscal
        - job/employment → economy_macro
        - energy → energy_transportation
        - tech/technology → technology
        - manufacturing → manufacturing
        - retail → retail_wholesale
        - biotech/health → life_sciences

        ## Output Format:
        Return your response as a JSON object with this exact structure:
        ```json
        {
        "relevant_categories": ["category1", "category2", "category3", ...]
        }
        ```

        ## Prioritization Rules:
        1. Always include "economy_macro" as a baseline category
        2. Prioritize categories based on the user's most prominent financial activities:
        - Student loans and mortgages (highest priority if present)
        - Investment and crypto accounts  
        - Credit cards and other loans
        - Bank accounts (lowest priority)
        3. Categories mentioned in the user statement should be highly prioritized
        4. Remove duplicates and order by relevance

        ## Example:
        Input:
        ```json
        {
        "accounts": [{"type": "investment"}, {"type": "crypto"}],
        "loans": [{"type": "student_loan"}],
        "investments": [{"type": "stock"}, {"type": "crypto"}]
        }
        ```
        User statement: "I want to pay off my student loans and invest in tech stocks"

        Output:
        ```json
        {
        "relevant_categories": [
            "economy_fiscal",
            "finance", 
            "blockchain",
            "earnings",
            "financial_markets",
            "technology",
            "ipo",
            "mergers_and_acquisitions",
            "economy_macro"
        ]
        }
        ```

        Now analyze the provided user financial data and statement to generate the most relevant news categories. 

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
        
    def _parse_input_data(self, accounts: str, loans: str, investments: str) -> Dict[str, Any]:
        """Parse and normalize input data into consistent format"""
        user_data = {}
        
        # Parse accounts
        if accounts:
            try:
                if accounts.startswith('[') or accounts.startswith('{'):
                    parsed_accounts = json.loads(accounts)
                else:
                    # Handle comma-separated string
                    parsed_accounts = [{"type": acc.strip()} for acc in accounts.split(',')]
                user_data['accounts'] = parsed_accounts
            except (json.JSONDecodeError, TypeError):
                user_data['accounts'] = [{"type": accounts}]
        
        # Parse loans  
        if loans:
            try:
                if loans.startswith('[') or loans.startswith('{'):
                    parsed_loans = json.loads(loans)
                else:
                    parsed_loans = [{"type": loan.strip()} for loan in loans.split(',')]
                user_data['loans'] = parsed_loans
            except (json.JSONDecodeError, TypeError):
                user_data['loans'] = [{"type": loans}]
        
        # Parse investments
        if investments:
            try:
                if investments.startswith('[') or investments.startswith('{'):
                    parsed_investments = json.loads(investments)
                else:
                    parsed_investments = [{"type": inv.strip()} for inv in investments.split(',')]
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
            system_prompt = self.prompt
            
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

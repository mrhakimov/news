"""
Plaid Financial Data Tool for Langflow

A custom Langflow tool component that integrates with Plaid API to retrieve
bank account balances and investment portfolio information for use by agents.
Includes automatic sandbox access token generation for easy testing.
"""

from typing import Dict, Any, List
import json
from datetime import datetime

from langflow.custom import Component
from langflow.io import StrInput, SecretStrInput, DropdownInput, BoolInput, Output
from langflow.schema import Data

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.products import Products


class PlaidFinancialTool(Component):
    """
    Plaid Financial Data Tool

    A tool that retrieves bank account balances and investment portfolio data
    from Plaid API for use by agents in financial analysis workflows.
    Can automatically generate sandbox access tokens for easy testing.
    """

    display_name = "Plaid Financial Tool"
    description = "Tool for agents to access bank accounts and investment portfolios via Plaid API"
    icon = "💰"
    name = "PlaidFinancialTool"
    documentation = "https://plaid.com/docs/"

    inputs = [
        SecretStrInput(
            name="client_id",
            display_name="Plaid Client ID",
            info="Your Plaid Client ID from the dashboard",
            required=True,
        ),
        SecretStrInput(
            name="secret_key",
            display_name="Plaid Secret Key",
            info="Your Plaid Secret Key from the dashboard",
            required=True,
        ),
        DropdownInput(
            name="environment",
            display_name="Environment",
            options=["sandbox", "development", "production"],
            value="sandbox",
            info="Plaid API environment to use",
            required=True,
        ),
        SecretStrInput(
            name="access_token",
            display_name="Access Token",
            info="User's Plaid access token (leave empty for auto-generation in sandbox)",
            required=False,
        ),
        BoolInput(
            name="auto_generate_sandbox_token",
            display_name="Auto-Generate Sandbox Token",
            info="Automatically create a sandbox access token if none provided (sandbox only)",
            value=True,
        ),
        DropdownInput(
            name="sandbox_institution",
            display_name="Sandbox Institution",
            options=["ins_109508", "ins_109509", "ins_109510", "ins_109511"],
            value="ins_109508",
            info="Sandbox institution to use for auto-generated tokens",
            advanced=True,
        ),
        StrInput(
            name="data_type",
            display_name="Data Type",
            info="Type of financial data to retrieve: accounts, balances, investments, or summary",
            value="summary",
            tool_mode=True,
        ),
        StrInput(
            name="output_format",
            display_name="Output Format",
            info="Format for the returned data: structured, json, or text",
            value="text",
            tool_mode=True,
        ),
    ]

    outputs = [Output(display_name="Plaid Tool", name="plaid", method="plaid")]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plaid_client = None
        self._generated_access_token = None
        self.status = "Initialized"
        # Don't log during init - component context not available yet

    def _safe_log(self, message: str):
        """Safely log a message only if component context is available"""
        try:
            self.log(message)
        except RuntimeError:
            # Component context not available, skip logging
            pass

    def _setup_plaid_client(self):
        """Initialize Plaid API client"""
        if self.plaid_client is not None:
            self._safe_log("Plaid client already initialized, skipping setup")
            return

        self._safe_log(f"Setting up Plaid client for environment: {self.environment}")

        try:
            # Use proper Plaid Environment constants
            if self.environment == "sandbox":
                host = plaid.Environment.Sandbox
            elif self.environment == "development":
                host = plaid.Environment.Development
            else:
                host = plaid.Environment.Production

            configuration = plaid.Configuration(
                host=host,
                api_key={
                    'clientId': self.client_id,
                    'secret': self.secret_key,
                }
            )

            api_client = plaid.ApiClient(configuration)
            self.plaid_client = plaid_api.PlaidApi(api_client)
            self.status = f"Connected to Plaid {self.environment} environment"
            self._safe_log(self.status)

        except Exception as e:
            error_msg = f"Failed to setup Plaid client: {str(e)}"
            self.status = error_msg
            self._safe_log(error_msg)
            raise ValueError(error_msg)

    def _generate_sandbox_access_token(self) -> str:
        """
        Generate a sandbox access token automatically
        Only works in sandbox environment
        """
        self._safe_log("Starting sandbox access token generation")

        if self.environment != "sandbox":
            error_msg = "Auto-generation only available in sandbox environment"
            self.status = error_msg
            self._safe_log(error_msg)
            raise ValueError(error_msg)

        if self._generated_access_token:
            self._safe_log("Using cached generated access token")
            return self._generated_access_token

        self._setup_plaid_client()

        try:
            # Step 1: Create sandbox public token
            institution_names = {
                "ins_109508": "First Platypus Bank",
                "ins_109509": "Second Platypus Bank", 
                "ins_109510": "Third Platypus Bank",
                "ins_109511": "Fourth Platypus Bank",
            }

            institution_id = getattr(self, "sandbox_institution", "ins_109508")
            institution_name = institution_names.get(institution_id, institution_id)
            self.status = f"Creating sandbox token for {institution_name}..."
            self._safe_log(self.status)

            # Use the sandbox_public_token_create method directly like in the working example
            sandbox_response = self.plaid_client.sandbox_public_token_create({
                'institution_id': institution_id,
                'initial_products': ['auth', 'transactions'],
            })
            public_token = sandbox_response['public_token']
            self._safe_log(f"Received public token: {public_token[:10]}...")

            # Step 2: Exchange public token for access token
            self._safe_log("Exchanging public token for access token")
            exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)

            exchange_response = self.plaid_client.item_public_token_exchange(exchange_request)
            access_token = exchange_response['access_token']
            self._safe_log(f"Received access token: {access_token[:10]}...")

            self._generated_access_token = access_token
            self.status = f"Generated sandbox access token for {institution_name}"
            self._safe_log(self.status)

            return access_token

        except Exception as e:
            error_msg = f"Failed to generate sandbox access token: {str(e)}"
            self.status = error_msg
            self._safe_log(error_msg)
            raise ValueError(error_msg)

    def _get_access_token(self) -> str:
        """
        Get access token - either provided or auto-generated
        """
        self._safe_log("Getting access token")

        # If access token is provided, use it
        if hasattr(self, "access_token") and self.access_token:
            self._safe_log("Using provided access token")
            return self.access_token

        # If in sandbox and auto-generation is enabled, create one
        if self.environment == "sandbox" and getattr(
            self, "auto_generate_sandbox_token", True
        ):
            self._safe_log("Auto-generating sandbox access token")
            return self._generate_sandbox_access_token()

        # Otherwise, raise error
        error_msg = "Access token is required. Either provide one or enable auto-generation for sandbox."
        self.status = error_msg
        self._safe_log(error_msg)
        raise ValueError(error_msg)

    def _get_accounts(self) -> List[Dict]:
        """Get basic account information"""
        self._safe_log("Retrieving account information")

        access_token = self._get_access_token()
        request = AccountsGetRequest(access_token=access_token)

        try:
            response = self.plaid_client.accounts_get(request)
            # Convert response to dict to access accounts properly
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            accounts_data = response_dict['accounts']
            
            self._safe_log(
                f"Retrieved {len(accounts_data)} accounts from Plaid API"
            )

            accounts = []
            for account in accounts_data:
                accounts.append(
                    {
                        "account_id": account["account_id"],
                        "name": account["name"],
                        "type": account["type"],
                        "subtype": account.get("subtype"),
                        "mask": account.get("mask"),
                    }
                )

            self.status = f"Successfully retrieved {len(accounts)} accounts"
            self._safe_log(self.status)
            return accounts

        except Exception as e:
            error_msg = f"Failed to get accounts: {str(e)}"
            self.status = error_msg
            self._safe_log(error_msg)
            raise

    def _get_balances(self) -> List[Dict]:
        """Get account balances"""
        self._safe_log("Retrieving account balances")

        access_token = self._get_access_token()
        request = AccountsBalanceGetRequest(access_token=access_token)

        try:
            response = self.plaid_client.accounts_balance_get(request)
            # Convert response to dict to access accounts properly like in working example
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            accounts_data = response_dict['accounts']
            
            self._safe_log(
                f"Retrieved balances for {len(accounts_data)} accounts from Plaid API"
            )

            balances = []
            for account in accounts_data:
                balance_data = {
                    "account_id": account["account_id"],
                    "account_name": account["name"],
                    "account_type": account["type"],
                    "current_balance": account["balances"]["current"],
                    "available_balance": account["balances"].get("available"),
                    "currency": account["balances"]["iso_currency_code"] or "USD",
                    "last_updated": datetime.now().isoformat(),
                }
                balances.append(balance_data)
                self._safe_log(
                    f"Account {account['name']}: {balance_data['current_balance']} {balance_data['currency']}"
                )

            self.status = (
                f"Successfully retrieved balances for {len(balances)} accounts"
            )
            self._safe_log(self.status)
            return balances

        except Exception as e:
            error_msg = f"Failed to get balances: {str(e)}"
            self.status = error_msg
            self._safe_log(error_msg)
            raise

    def _get_investments(self) -> Dict:
        """Get investment portfolio data"""
        self._safe_log("Retrieving investment portfolio data")

        access_token = self._get_access_token()
        request = InvestmentsHoldingsGetRequest(access_token=access_token)

        try:
            response = self.plaid_client.investments_holdings_get(request)
            # Convert response to dict to access data properly
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            holdings_data = response_dict['holdings']
            securities_data = response_dict['securities']
            
            self._safe_log(
                f"Retrieved {len(holdings_data)} holdings and {len(securities_data)} securities from Plaid API"
            )

            securities = {sec["security_id"]: sec for sec in securities_data}

            holdings = []
            total_value = 0.0

            for holding in holdings_data:
                security = securities.get(holding["security_id"])
                if not security:
                    self._safe_log(
                        f"Warning: Security not found for holding: {holding['security_id']}"
                    )
                    continue

                market_value = holding["quantity"] * holding["institution_price"]
                total_value += market_value

                holding_data = {
                    "account_id": holding["account_id"],
                    "security_name": security["name"],
                    "ticker_symbol": security.get("ticker_symbol"),
                    "quantity": holding["quantity"],
                    "current_price": holding["institution_price"],
                    "market_value": market_value,
                    "cost_basis": holding.get("cost_basis"),
                    "currency": holding["iso_currency_code"] or "USD",
                }
                holdings.append(holding_data)
                self._safe_log(
                    f"Holding {security['name']}: ${market_value:,.2f} {holding_data['currency']}"
                )

            result = {
                "total_value": total_value,
                "holdings_count": len(holdings),
                "holdings": holdings,
                "last_updated": datetime.now().isoformat(),
            }

            self.status = f"Successfully retrieved {len(holdings)} holdings worth ${total_value:,.2f}"
            self._safe_log(self.status)
            return result

        except Exception as e:
            error_msg = f"Failed to get investments: {str(e)}"
            self.status = error_msg
            self._safe_log(error_msg)
            raise

    def _get_summary(self) -> Dict:
        """Get comprehensive financial summary"""
        self._safe_log("Generating comprehensive financial summary")

        try:
            balances = self._get_balances()

            banking_total = sum(
                balance["current_balance"]
                for balance in balances
                if balance["account_type"] in ["depository"]
            )

            credit_total = sum(
                abs(balance["current_balance"])
                for balance in balances
                if balance["account_type"] == "credit"
            )

            self._safe_log(
                f"Banking calculations - Deposits: ${banking_total:,.2f}, Credit: ${credit_total:,.2f}"
            )

            summary = {
                "timestamp": datetime.now().isoformat(),
                "banking": {
                    "total_deposits": banking_total,
                    "total_credit": credit_total,
                    "account_count": len(balances),
                    "accounts": balances,
                },
            }

            try:
                self._safe_log("Attempting to retrieve investment data for summary")
                investments = self._get_investments()
                summary["investments"] = investments
                net_worth = banking_total - credit_total + investments["total_value"]
                summary["net_worth"] = net_worth
                self._safe_log(
                    f"Net worth calculation with investments: ${net_worth:,.2f}"
                )
            except Exception as e:
                self._safe_log(f"Could not retrieve investment data: {str(e)}")
                summary["net_worth"] = banking_total - credit_total
                summary["investments"] = None
                self._safe_log(
                    f"Net worth calculation without investments: ${summary['net_worth']:,.2f}"
                )

            self.status = (
                f"Generated financial summary - Net worth: ${summary['net_worth']:,.2f}"
            )
            self._safe_log(self.status)
            return summary

        except Exception as e:
            error_msg = f"Failed to generate summary: {str(e)}"
            self.status = error_msg
            self._safe_log(error_msg)
            raise

    def _format_output(self, data: Any, format_type: str) -> Any:
        """Format output based on selected format"""
        self._safe_log(f"Formatting output as {format_type}")

        if format_type == "json":
            return json.dumps(data, indent=2, default=str)
        elif format_type == "text":
            return self._format_as_text(data)
        else:
            return data

    def _format_as_text(self, data: Any, data_type: str) -> str:
        """Format data as human-readable text"""
        self._safe_log(f"Formatting {data_type} data as human-readable text")

        if data_type == "accounts":
            text = "ACCOUNT INFORMATION\n" + "=" * 50 + "\n"
            for account in data:
                text += f"Account: {account['name']}\n"
                text += f"Type: {account['type']}\n"
                text += f"ID: {account['account_id']}\n"
                text += "-" * 30 + "\n"

        elif data_type == "balances":
            text = "ACCOUNT BALANCES\n" + "=" * 50 + "\n"
            for balance in data:
                text += f"Account: {balance['account_name']}\n"
                text += f"Balance: {balance['currency']} {balance['current_balance']:,.2f}\n"
                if balance["available_balance"]:
                    text += f"Available: {balance['currency']} {balance['available_balance']:,.2f}\n"
                text += "-" * 30 + "\n"

        elif data_type == "investments":
            text = "INVESTMENT PORTFOLIO\n" + "=" * 50 + "\n"
            text += f"Total Value: ${data['total_value']:,.2f}\n"
            text += f"Holdings: {data['holdings_count']}\n"
            text += "-" * 50 + "\n"

            for holding in data["holdings"][:5]:
                text += f"Security: {holding['security_name']}\n"
                if holding["ticker_symbol"]:
                    text += f"Ticker: {holding['ticker_symbol']}\n"
                text += f"Value: ${holding['market_value']:,.2f}\n"
                text += "-" * 30 + "\n"

        elif data_type == "summary":
            text = "FINANCIAL SUMMARY\n" + "=" * 50 + "\n"
            text += f"Net Worth: ${data['net_worth']:,.2f}\n"
            text += f"Bank Deposits: ${data['banking']['total_deposits']:,.2f}\n"
            text += f"Credit Balances: ${data['banking']['total_credit']:,.2f}\n"

            if data["investments"]:
                text += (
                    f"Investment Value: ${data['investments']['total_value']:,.2f}\n"
                )

            text += f"Bank Accounts: {data['banking']['account_count']}\n"

        else:
            text = str(data)

        self._safe_log(f"Generated {len(text)} characters of formatted text output")
        return text

    def get_financial_data(
        self, data_type: str = "summary", output_format: str = "text"
    ) -> str:
        """
        Tool method to retrieve financial data from Plaid API

        Args:
            data_type: Type of data to retrieve (accounts, balances, investments, summary)
            output_format: Format of output (structured, json, text)

        Returns:
            Formatted financial data as string
        """
        self._safe_log(
            f"get_financial_data() called with data_type='{data_type}', output_format='{output_format}'"
        )

        try:
            self._setup_plaid_client()

            # Validate data_type
            valid_types = ["accounts", "balances", "investments", "summary"]
            if data_type not in valid_types:
                self._safe_log(
                    f"Invalid data_type '{data_type}', defaulting to 'summary'"
                )
                data_type = "summary"

            # Validate output_format
            valid_formats = ["structured", "json", "text"]
            if output_format not in valid_formats:
                self._safe_log(
                    f"Invalid output_format '{output_format}', defaulting to 'text'"
                )
                output_format = "text"

            self._safe_log(
                f"Processing request for {data_type} data in {output_format} format"
            )

            if data_type == "accounts":
                raw_data = self._get_accounts()

            elif data_type == "balances":
                raw_data = self._get_balances()

            elif data_type == "investments":
                raw_data = self._get_investments()

            elif data_type == "summary":
                raw_data = self._get_summary()

            else:
                raise ValueError(f"Unsupported data type: {data_type}")

            if output_format == "text":
                result = self._format_as_text(raw_data, data_type)
            elif output_format == "json":
                result = json.dumps(raw_data, indent=2, default=str)
            else:
                result = str(raw_data)

            self.status = (
                f"Successfully processed {data_type} request ({len(result)} characters)"
            )
            self._safe_log(self.status)
            return result

        except Exception as e:
            error_msg = f"Failed to retrieve {data_type}: {str(e)}"
            self.status = error_msg
            self._safe_log(error_msg)
            # Return structured error data instead of raising exception
            return json.dumps(
                {
                    "error": error_msg,
                    "data_type": data_type,
                    "timestamp": datetime.now().isoformat(),
                },
                indent=2,
            )

    def plaid(self) -> Data:
        """Plaid tool for agent"""

        tool_data = {
            "data": self.get_financial_data(self.data_type, self.output_format)
        }

        return Data(data=tool_data)

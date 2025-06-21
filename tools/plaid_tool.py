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
from plaid.model.liabilities_get_request import LiabilitiesGetRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)


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
            info="Type of financial data to retrieve: accounts, balances, investments, liabilities, or summary",
            value="summary",
            tool_mode=True,
        ),
        StrInput(
            name="output_format",
            display_name="Output Format",
            info="Format for the returned data: structured or json",
            value="structured",
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

    def _setup_plaid_client(self):
        """Initialize Plaid API client"""
        if self.plaid_client is not None:
            return

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

        except Exception as e:
            error_msg = f"Failed to setup Plaid client: {str(e)}"
            self.status = error_msg
            raise ValueError(error_msg)

    def _generate_sandbox_access_token(self) -> str:
        """
        Generate a sandbox access token automatically
        Only works in sandbox environment
        """

        if self.environment != "sandbox":
            error_msg = "Auto-generation only available in sandbox environment"
            self.status = error_msg
            raise ValueError(error_msg)

        if self._generated_access_token:
            return self._generated_access_token

        self._setup_plaid_client()

        try:

            institution_id = self.sandbox_institution

            sandbox_response = self.plaid_client.sandbox_public_token_create({
                'institution_id': institution_id,
                'initial_products': ['auth', 'transactions', 'investments', 'liabilities'],
            })
            public_token = sandbox_response['public_token']

            # Step 2: Exchange public token for access token
            exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
            exchange_response = self.plaid_client.item_public_token_exchange(exchange_request)
            access_token = exchange_response['access_token']

            self._generated_access_token = access_token

            return access_token

        except Exception as e:
            error_msg = f"Failed to generate sandbox access token: {str(e)}"
            self.status = error_msg
            raise ValueError(error_msg)

    def _get_access_token(self) -> str:
        """
        Get access token - either provided or auto-generated
        """

        # If access token is provided, use it
        if hasattr(self, "access_token") and self.access_token:
            return self.access_token

        # If in sandbox and auto-generation is enabled, create one
        if self.environment == "sandbox" and getattr(
            self, "auto_generate_sandbox_token", True
        ):
            return self._generate_sandbox_access_token()

        # Otherwise, raise error
        error_msg = "Access token is required. Either provide one or enable auto-generation for sandbox."
        self.status = error_msg
        raise ValueError(error_msg)

    def _get_accounts(self) -> List[Dict]:
        """Get basic account information"""

        access_token = self._get_access_token()
        request = AccountsGetRequest(access_token=access_token)

        try:
            response = self.plaid_client.accounts_get(request)
            # Convert response to dict to access accounts properly
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            accounts_data = response_dict['accounts']
            

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
            return accounts

        except Exception as e:
            error_msg = f"Failed to get accounts: {str(e)}"
            self.status = error_msg
            raise

    def _get_balances(self) -> List[Dict]:
        """Get account balances"""

        access_token = self._get_access_token()
        request = AccountsBalanceGetRequest(access_token=access_token)

        try:
            response = self.plaid_client.accounts_balance_get(request)
            # Convert response to dict to access accounts properly like in working example
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            accounts_data = response_dict['accounts']
            

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

            self.status = (
                f"Successfully retrieved balances for {len(balances)} accounts"
            )
            return balances

        except Exception as e:
            error_msg = f"Failed to get balances: {str(e)}"
            self.status = error_msg
            raise

    def _get_investments(self) -> Dict:
        """Get investment portfolio data"""

        access_token = self._get_access_token()
        request = InvestmentsHoldingsGetRequest(access_token=access_token)

        try:
            response = self.plaid_client.investments_holdings_get(request)
            # Convert response to dict to access data properly
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            holdings_data = response_dict.get('holdings', [])
            securities_data = response_dict.get('securities', [])
            accounts_data = response_dict.get('accounts', [])
            
            if not holdings_data:
                return {
                    "total_value": 0.0,
                    "holdings_count": 0,
                    "holdings": [],
                    "accounts": [],
                    "last_updated": datetime.now().isoformat(),
                }

            # Create lookup dictionaries
            securities = {sec["security_id"]: sec for sec in securities_data}
            accounts_dict = {acc["account_id"]: acc for acc in accounts_data}

            holdings = []
            total_value = 0.0
            total_cost_basis = 0.0
            accounts_summary = {}

            for holding in holdings_data:
                security = securities.get(holding["security_id"])
                if not security:
                    continue

                # Calculate values
                quantity = holding.get("quantity", 0)
                institution_price = holding.get("institution_price", 0)
                market_value = quantity * institution_price
                cost_basis = holding.get("cost_basis", 0)
                
                total_value += market_value
                if cost_basis:
                    total_cost_basis += cost_basis

                # Account information
                account_id = holding["account_id"]
                account_info = accounts_dict.get(account_id, {})
                account_name = account_info.get("name", f"Investment Account {account_id[-4:]}")

                # Track account summary
                if account_id not in accounts_summary:
                    accounts_summary[account_id] = {
                        "account_id": account_id,
                        "account_name": account_name,
                        "total_value": 0.0,
                        "holdings_count": 0
                    }
                accounts_summary[account_id]["total_value"] += market_value
                accounts_summary[account_id]["holdings_count"] += 1

                holding_data = {
                    "account_id": account_id,
                    "account_name": account_name,
                    "security_id": holding["security_id"],
                    "security_name": security.get("name", "Unknown Security"),
                    "ticker_symbol": security.get("ticker_symbol"),
                    "security_type": security.get("type"),
                    "quantity": quantity,
                    "current_price": institution_price,
                    "market_value": market_value,
                    "cost_basis": cost_basis,
                    "currency": holding.get("iso_currency_code") or holding.get("unofficial_currency_code") or "USD",
                }

                # Calculate gain/loss if cost basis is available
                if cost_basis and cost_basis > 0:
                    gain_loss = market_value - cost_basis
                    gain_loss_pct = (gain_loss / cost_basis) * 100
                    holding_data["gain_loss"] = gain_loss
                    holding_data["gain_loss_percent"] = gain_loss_pct

                holdings.append(holding_data)

            # Prepare result with comprehensive data
            result = {
                "total_value": total_value,
                "total_cost_basis": total_cost_basis if total_cost_basis > 0 else None,
                "holdings_count": len(holdings),
                "accounts_count": len(accounts_summary),
                "holdings": holdings,
                "accounts": list(accounts_summary.values()),
                "last_updated": datetime.now().isoformat(),
            }

            # Add overall portfolio performance if cost basis is available
            if total_cost_basis > 0:
                total_gain_loss = total_value - total_cost_basis
                total_gain_loss_pct = (total_gain_loss / total_cost_basis) * 100
                result["total_gain_loss"] = total_gain_loss
                result["total_gain_loss_percent"] = total_gain_loss_pct

            self.status = f"Successfully retrieved {len(holdings)} holdings across {len(accounts_summary)} accounts worth ${total_value:,.2f}"
            return result

        except Exception as e:
            error_msg = f"Failed to get investments: {str(e)}"
            self.status = error_msg
            raise

    def _get_liabilities(self) -> Dict:
        """Get liabilities data (loans, mortgages, credit cards, etc.)"""

        access_token = self._get_access_token()
        request = LiabilitiesGetRequest(access_token=access_token)

        try:
            response = self.plaid_client.liabilities_get(request)
            # Convert response to dict to access data properly
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            liabilities_data = response_dict.get('liabilities', {})
            accounts_data = response_dict.get('accounts', [])
            
            # Create accounts lookup
            accounts_dict = {acc["account_id"]: acc for acc in accounts_data}
            
            # Process different types of liabilities
            result = {
                "total_debt": 0.0,
                "liability_count": 0,
                "accounts_count": len(accounts_data),
                "mortgages": [],
                "student_loans": [],
                "credit_cards": [],
                "other_liabilities": [],
                "last_updated": datetime.now().isoformat(),
            }

            # Process mortgages
            if liabilities_data.get('mortgage'):
                for mortgage in liabilities_data['mortgage']:
                    account_id = mortgage.get('account_id')
                    account_info = accounts_dict.get(account_id, {})
                    
                    mortgage_data = {
                        "account_id": account_id,
                        "account_name": account_info.get("name", f"Mortgage {account_id[-4:] if account_id else 'Unknown'}"),
                        "current_balance": mortgage.get('current_late_fee', 0) + mortgage.get('escrow_balance', 0),
                        "last_payment_amount": mortgage.get('last_payment_amount'),
                        "last_payment_date": mortgage.get('last_payment_date'),
                        "next_payment_due_date": mortgage.get('next_payment_due_date'),
                        "ytd_interest_paid": mortgage.get('ytd_interest_paid'),
                        "ytd_principal_paid": mortgage.get('ytd_principal_paid'),
                        "interest_rate": mortgage.get('interest_rate', {}).get('percentage'),
                        "loan_type": mortgage.get('loan_type_description'),
                        "maturity_date": mortgage.get('maturity_date'),
                        "origination_date": mortgage.get('origination_date'),
                        "origination_principal_amount": mortgage.get('origination_principal_amount'),
                        "property_address": mortgage.get('property_address'),
                    }
                    
                    # Add to total debt (using account balance if available)
                    if account_info.get('balances', {}).get('current'):
                        debt_amount = abs(account_info['balances']['current'])
                        mortgage_data['outstanding_balance'] = debt_amount
                        result["total_debt"] += debt_amount
                    
                    result["mortgages"].append(mortgage_data)
                    result["liability_count"] += 1

            # Process student loans
            if liabilities_data.get('student'):
                for loan in liabilities_data['student']:
                    account_id = loan.get('account_id')
                    account_info = accounts_dict.get(account_id, {})
                    
                    loan_data = {
                        "account_id": account_id,
                        "account_name": account_info.get("name", f"Student Loan {account_id[-4:] if account_id else 'Unknown'}"),
                        "loan_name": loan.get('loan_name'),
                        "loan_status": loan.get('loan_status', {}).get('type'),
                        "minimum_payment_amount": loan.get('minimum_payment_amount'),
                        "next_payment_due_date": loan.get('next_payment_due_date'),
                        "origination_date": loan.get('origination_date'),
                        "origination_principal_amount": loan.get('origination_principal_amount'),
                        "outstanding_interest_amount": loan.get('outstanding_interest_amount'),
                        "payment_reference_number": loan.get('payment_reference_number'),
                        "interest_rate": loan.get('interest_rate_percentage'),
                        "is_overdue": loan.get('is_overdue'),
                        "last_payment_amount": loan.get('last_payment_amount'),
                        "last_payment_date": loan.get('last_payment_date'),
                        "last_statement_issue_date": loan.get('last_statement_issue_date'),
                        "guarantor": loan.get('guarantor'),
                        "repayment_plan": loan.get('repayment_plan', {}).get('description'),
                        "servicer_address": loan.get('servicer_address'),
                    }
                    
                    # Add to total debt (using account balance if available)
                    if account_info.get('balances', {}).get('current'):
                        debt_amount = abs(account_info['balances']['current'])
                        loan_data['outstanding_balance'] = debt_amount
                        result["total_debt"] += debt_amount
                    
                    result["student_loans"].append(loan_data)
                    result["liability_count"] += 1

            # Process credit cards (from accounts with credit type)
            credit_accounts = [acc for acc in accounts_data if acc.get('type') == 'credit']
            for account in credit_accounts:
                balances = account.get('balances', {})
                credit_data = {
                    "account_id": account['account_id'],
                    "account_name": account.get('name', f"Credit Card {account['account_id'][-4:]}"),
                    "current_balance": abs(balances.get('current', 0)),
                    "available_credit": balances.get('available'),
                    "credit_limit": balances.get('limit'),
                    "currency": balances.get('iso_currency_code') or 'USD',
                    "last_updated": datetime.now().isoformat(),
                }
                
                # Calculate utilization if limit is available
                if credit_data["credit_limit"] and credit_data["credit_limit"] > 0:
                    utilization = (credit_data["current_balance"] / credit_data["credit_limit"]) * 100
                    credit_data["utilization_percentage"] = round(utilization, 2)
                
                result["credit_cards"].append(credit_data)
                result["total_debt"] += credit_data["current_balance"]
                result["liability_count"] += 1

            # Add any remaining liability accounts that aren't mortgages or student loans
            other_liability_accounts = [
                acc for acc in accounts_data 
                if acc.get('type') == 'loan' and acc['account_id'] not in 
                [m.get('account_id') for m in result["mortgages"]] +
                [s.get('account_id') for s in result["student_loans"]]
            ]
            
            for account in other_liability_accounts:
                balances = account.get('balances', {})
                other_data = {
                    "account_id": account['account_id'],
                    "account_name": account.get('name', f"Loan {account['account_id'][-4:]}"),
                    "account_subtype": account.get('subtype'),
                    "current_balance": abs(balances.get('current', 0)),
                    "currency": balances.get('iso_currency_code') or 'USD',
                    "last_updated": datetime.now().isoformat(),
                }
                
                result["other_liabilities"].append(other_data)
                result["total_debt"] += other_data["current_balance"]
                result["liability_count"] += 1

            self.status = f"Successfully retrieved {result['liability_count']} liabilities with total debt of ${result['total_debt']:,.2f}"
            return result

        except Exception as e:
            error_msg = f"Failed to get liabilities: {str(e)}"
            self.status = error_msg
            raise

    def _get_summary(self) -> Dict:
        """Get comprehensive financial summary"""

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

            summary = {
                "timestamp": datetime.now().isoformat(),
                "banking": {
                    "total_deposits": banking_total,
                    "total_credit": credit_total,
                    "account_count": len(balances),
                    "accounts": balances,
                },
            }

            # Initialize investment and liability values for net worth calculation
            investment_value = 0
            total_liabilities = 0
            
            try:
                investments = self._get_investments()
                summary["investments"] = investments
                investment_value = investments["total_value"]
                
                # Add investment performance summary if available
                if investments.get("total_cost_basis"):
                    summary["investment_performance"] = {
                        "total_gain_loss": investments.get("total_gain_loss", 0),
                        "total_gain_loss_percent": investments.get("total_gain_loss_percent", 0)
                    }
                
            except Exception as e:
                summary["investments"] = None
                summary["investment_performance"] = None

            try:
                liabilities = self._get_liabilities()
                summary["liabilities"] = liabilities
                total_liabilities = liabilities["total_debt"]
                
            except Exception as e:
                summary["liabilities"] = None

            # Calculate net worth: Assets (banking + investments) - Liabilities (credit + other debt)
            net_worth = banking_total - credit_total + investment_value - total_liabilities
            summary["net_worth"] = net_worth

            self.status = (
                f"Generated financial summary - Net worth: ${summary['net_worth']:,.2f}"
            )
            return summary

        except Exception as e:
            error_msg = f"Failed to generate summary: {str(e)}"
            self.status = error_msg
            raise

    def get_financial_data(
        self, data_type: str = "summary", output_format: str = "structured"
    ) -> Any:
        """
        Tool method to retrieve financial data from Plaid API

        Args:
            data_type: Type of data to retrieve (accounts, balances, investments, summary)
            output_format: Format of output (structured, json)

        Returns:
            Financial data as structured dict/list or JSON string
        """

        try:
            self._setup_plaid_client()

            # Validate data_type
            valid_types = ["accounts", "balances", "investments", "liabilities", "summary"]
            if data_type not in valid_types:
                data_type = "summary"

            # Validate output_format
            valid_formats = ["structured", "json"]
            if output_format not in valid_formats:
                output_format = "structured"

            if data_type == "accounts":
                raw_data = self._get_accounts()

            elif data_type == "balances":
                raw_data = self._get_balances()

            elif data_type == "investments":
                raw_data = self._get_investments()

            elif data_type == "liabilities":
                raw_data = self._get_liabilities()

            elif data_type == "summary":
                raw_data = self._get_summary()

            else:
                raise ValueError(f"Unsupported data type: {data_type}")

            if output_format == "json":
                result = json.dumps(raw_data, indent=2, default=str)
            else:  # structured format
                result = raw_data

            self.status = (
                f"Successfully processed {data_type} request ({len(result)} characters)"
            )
            return result

        except Exception as e:
            error_msg = f"Failed to retrieve {data_type}: {str(e)}"
            self.status = error_msg
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

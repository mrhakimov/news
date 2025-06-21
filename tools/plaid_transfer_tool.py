"""
Plaid Transfer Tool for Langflow

A custom Langflow tool component that integrates with Plaid Transfer API to enable
money transfers between bank accounts. Supports ACH transfers, authorization,
and transfer status tracking for use by agents.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from langflow.custom import Component
from langflow.io import StrInput, SecretStrInput, DropdownInput, BoolInput, FloatInput, Output
from langflow.schema import Data

import plaid
from plaid.api import plaid_api
from plaid.model.transfer_intent_create_request import TransferIntentCreateRequest
from plaid.model.transfer_create_request import TransferCreateRequest
from plaid.model.transfer_authorization_create_request import TransferAuthorizationCreateRequest
from plaid.model.transfer_get_request import TransferGetRequest
from plaid.model.transfer_list_request import TransferListRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transfer_intent_create_mode import TransferIntentCreateMode
from plaid.model.transfer_user_in_request import TransferUserInRequest
from plaid.model.ach_class import ACHClass
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.transfer_intent_create_network import TransferIntentCreateNetwork


class PlaidTransferTool(Component):
    """
    Plaid Transfer Tool

    A tool that enables agents to perform money transfers between bank accounts
    using the Plaid Transfer API. Supports ACH transfers with proper authorization
    and status tracking.
    """

    display_name = "Plaid Transfer Tool"
    description = "Tool for agents to perform money transfers between bank accounts via Plaid Transfer API"
    icon = "💸"
    name = "PlaidTransferTool"
    documentation = "https://plaid.com/docs/transfer/"

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
            info="User's Plaid access token for the source account (leave empty for auto-generation in sandbox)",
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
            name="action",
            display_name="Action",
            info="Transfer action: create_intent, authorize, execute, status, list, or get_accounts",
            value="get_accounts",
            tool_mode=True,
        ),
        StrInput(
            name="source_account_id",
            display_name="Source Account ID",
            info="Account ID to transfer money from",
            required=False,
            tool_mode=True,
        ),
        StrInput(
            name="destination_account_id",
            display_name="Destination Account ID", 
            info="Account ID to transfer money to (for internal transfers)",
            required=False,
            tool_mode=True,
        ),
        FloatInput(
            name="amount",
            display_name="Transfer Amount",
            info="Amount to transfer in USD",
            required=False,
            tool_mode=True,
        ),
        StrInput(
            name="description",
            display_name="Transfer Description",
            info="Description for the transfer (max 15 characters)",
            value="Agent transfer",
            tool_mode=True,
        ),
        DropdownInput(
            name="transfer_type",
            display_name="Transfer Type",
            options=["debit", "credit"],
            value="debit",
            info="Type of transfer (debit from source, credit to destination)",
            advanced=True,
        ),
        DropdownInput(
            name="ach_class",
            display_name="ACH Class",
            options=["ppd", "web", "tel", "ccd"],
            value="ppd",
            info="ACH class for the transfer",
            advanced=True,
        ),
        StrInput(
            name="transfer_intent_id",
            display_name="Transfer Intent ID",
            info="ID of existing transfer intent (for authorize/execute actions)",
            required=False,
            tool_mode=True,
        ),
        StrInput(
            name="transfer_id",
            display_name="Transfer ID",
            info="ID of existing transfer (for status check)",
            required=False,
            tool_mode=True,
        ),
        BoolInput(
            name="require_guarantee",
            display_name="Require Guarantee",
            info="Whether to require Plaid guarantee for the transfer",
            value=False,
            advanced=True,
        ),
        StrInput(
            name="user_id",
            display_name="User ID",
            info="Unique identifier for the user making the transfer",
            value="agent_user",
            tool_mode=True,
        ),
    ]

    outputs = [Output(display_name="Transfer Tool", name="transfer", method="transfer")]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plaid_client = None
        self._generated_access_token = None
        self._last_transfer_intent_id = None  # Store last created intent ID
        self.status = "Initialized"

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
                'initial_products': ['auth', 'transactions', 'investments', 'liabilities', 'transfer'],
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
        """Get available accounts for transfer"""
        self._setup_plaid_client()
        
        try:
            access_token = self._get_access_token()
            request = AccountsGetRequest(access_token=access_token)
            response = self.plaid_client.accounts_get(request)
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            accounts_data = response_dict['accounts']

            accounts = []
            for account in accounts_data:
                account_info = {
                    "account_id": account["account_id"],
                    "name": account["name"],
                    "type": account["type"],
                    "subtype": account.get("subtype"),
                    "mask": account.get("mask"),
                    "current_balance": account["balances"]["current"],
                    "available_balance": account["balances"].get("available"),
                    "currency": account["balances"]["iso_currency_code"] or "USD",
                }
                accounts.append(account_info)

            self.status = f"Retrieved {len(accounts)} accounts for transfer"
            return accounts

        except Exception as e:
            error_msg = f"Failed to get accounts: {str(e)}"
            self.status = error_msg
            raise

    def _create_transfer_intent(self) -> Dict:
        """Create a transfer intent"""
        self._setup_plaid_client()
        
        if not self.source_account_id or not self.amount:
            raise ValueError("Source account ID and amount are required for creating transfer intent")

        try:
            access_token = self._get_access_token()
            
            # Convert amount to decimal string format required by Plaid (e.g., "200.00")
            amount_decimal = f"{self.amount:.2f}"
            
            # Ensure description meets Plaid's 15-character limit
            description = self.description[:15] if self.description else "Transfer"
            
            # Create transfer user
            user = TransferUserInRequest(legal_name=f"User {self.user_id}")
            
            # Map ACH class using proper enum values
            ach_class_map = {
                "ppd": ACHClass('ppd'),
                "web": ACHClass('web'), 
                "tel": ACHClass('tel'),
                "ccd": ACHClass('ccd')
            }
            ach_class = ach_class_map.get(self.ach_class, ACHClass('ppd'))
            
            request = TransferIntentCreateRequest(
                account_id=self.source_account_id,
                amount=amount_decimal,
                mode=TransferIntentCreateMode('PAYMENT'),
                network=TransferIntentCreateNetwork('ach'),
                ach_class=ach_class,
                user=user,
                description="Agent",
                require_guarantee=self.require_guarantee
            )

            response = self.plaid_client.transfer_intent_create(request)
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            
            intent_data = {
                "transfer_intent_id": response_dict["transfer_intent"]["id"],
                "status": response_dict["transfer_intent"]["status"],
                "account_id": response_dict["transfer_intent"]["account_id"],
                "amount": float(response_dict["transfer_intent"]["amount"]),
                "description": response_dict["transfer_intent"]["description"],
                "mode": response_dict["transfer_intent"]["mode"],
                "network": response_dict["transfer_intent"]["network"],
                "ach_class": response_dict["transfer_intent"]["ach_class"],
                "created": response_dict["transfer_intent"]["created"],
                "require_guarantee": response_dict["transfer_intent"].get("require_guarantee", False),
            }

            self.status = f"Created transfer intent {intent_data['transfer_intent_id']} for ${intent_data['amount']:.2f}"
            
            # Store the intent ID for potential reuse in authorize/execute
            self._last_transfer_intent_id = intent_data['transfer_intent_id']
            
            return intent_data

        except Exception as e:
            error_msg = f"Failed to create transfer intent: {str(e)}"
            self.status = error_msg
            raise

    def _authorize_transfer(self) -> Dict:
        """Authorize a transfer intent"""
        self._setup_plaid_client()
        
        # Use provided intent ID or fall back to last created one
        intent_id = self.transfer_intent_id or self._last_transfer_intent_id
        
        if not intent_id:
            raise ValueError("Transfer intent ID is required for authorization. Either provide transfer_intent_id or create an intent first.")

        try:
            access_token = self._get_access_token()
            request = TransferAuthorizationCreateRequest(
                access_token=access_token,
                transfer_intent_id=intent_id
            )

            response = self.plaid_client.transfer_authorization_create(request)
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            
            auth_data = {
                "authorization_id": response_dict["authorization"]["id"],
                "transfer_intent_id": response_dict["authorization"]["transfer_intent_id"],
                "status": response_dict["authorization"]["status"],
                "decision": response_dict["authorization"]["decision"],
                "decision_rationale": response_dict["authorization"].get("decision_rationale"),
                "guarantee_decision": response_dict["authorization"].get("guarantee_decision"),
                "guarantee_decision_rationale": response_dict["authorization"].get("guarantee_decision_rationale"),
                "created": response_dict["authorization"]["created"],
            }

            self.status = f"Authorization {auth_data['authorization_id']}: {auth_data['decision']}"
            return auth_data

        except Exception as e:
            error_msg = f"Failed to authorize transfer: {str(e)}"
            self.status = error_msg
            raise

    def _execute_transfer(self) -> Dict:
        """Execute a transfer"""
        self._setup_plaid_client()
        
        # Use provided intent ID or fall back to last created one
        intent_id = self.transfer_intent_id or self._last_transfer_intent_id
        
        if not intent_id:
            raise ValueError("Transfer intent ID is required for execution. Either provide transfer_intent_id or create an intent first.")

        try:
            access_token = self._get_access_token()
            request = TransferCreateRequest(
                access_token=access_token,
                transfer_intent_id=intent_id
            )

            response = self.plaid_client.transfer_create(request)
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            
            transfer_data = {
                "transfer_id": response_dict["transfer"]["id"],
                "transfer_intent_id": response_dict["transfer"]["transfer_intent_id"],
                "authorization_id": response_dict["transfer"]["authorization_id"],
                "account_id": response_dict["transfer"]["account_id"],
                "amount": float(response_dict["transfer"]["amount"]),
                "description": response_dict["transfer"]["description"],
                "status": response_dict["transfer"]["status"],
                "type": response_dict["transfer"]["type"],
                "network": response_dict["transfer"]["network"],
                "ach_class": response_dict["transfer"]["ach_class"],
                "created": response_dict["transfer"]["created"],
                "originated_account_id": response_dict["transfer"].get("originated_account_id"),
            }

            self.status = f"Executed transfer {transfer_data['transfer_id']} for ${transfer_data['amount']:.2f}"
            return transfer_data

        except Exception as e:
            error_msg = f"Failed to execute transfer: {str(e)}"
            self.status = error_msg
            raise

    def _get_transfer_status(self) -> Dict:
        """Get status of a specific transfer"""
        self._setup_plaid_client()
        
        if not self.transfer_id:
            raise ValueError("Transfer ID is required for status check")

        try:
            request = TransferGetRequest(transfer_id=self.transfer_id)
            response = self.plaid_client.transfer_get(request)
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            
            transfer_data = {
                "transfer_id": response_dict["transfer"]["id"],
                "transfer_intent_id": response_dict["transfer"]["transfer_intent_id"],
                "authorization_id": response_dict["transfer"]["authorization_id"],
                "account_id": response_dict["transfer"]["account_id"],
                "amount": float(response_dict["transfer"]["amount"]),
                "description": response_dict["transfer"]["description"],
                "status": response_dict["transfer"]["status"],
                "type": response_dict["transfer"]["type"],
                "network": response_dict["transfer"]["network"],
                "ach_class": response_dict["transfer"]["ach_class"],
                "created": response_dict["transfer"]["created"],
                "originated_account_id": response_dict["transfer"].get("originated_account_id"),
                "failure_reason": response_dict["transfer"].get("failure_reason"),
            }

            self.status = f"Transfer {transfer_data['transfer_id']} status: {transfer_data['status']}"
            return transfer_data

        except Exception as e:
            error_msg = f"Failed to get transfer status: {str(e)}"
            self.status = error_msg
            raise

    def _list_transfers(self) -> List[Dict]:
        """List recent transfers"""
        self._setup_plaid_client()
        
        try:
            access_token = self._get_access_token()
            request = TransferListRequest(access_token=access_token)
            response = self.plaid_client.transfer_list(request)
            response_dict = response.to_dict() if hasattr(response, 'to_dict') else response
            
            transfers = []
            for transfer in response_dict.get("transfers", []):
                transfer_data = {
                    "transfer_id": transfer["id"],
                    "transfer_intent_id": transfer["transfer_intent_id"],
                    "account_id": transfer["account_id"],
                    "amount": float(transfer["amount"]),
                    "description": transfer["description"],
                    "status": transfer["status"],
                    "type": transfer["type"],
                    "network": transfer["network"],
                    "created": transfer["created"],
                    "failure_reason": transfer.get("failure_reason"),
                }
                transfers.append(transfer_data)

            self.status = f"Retrieved {len(transfers)} transfers"
            return transfers

        except Exception as e:
            error_msg = f"Failed to list transfers: {str(e)}"
            self.status = error_msg
            raise

    def perform_transfer_action(self, action: str = "get_accounts") -> Any:
        """
        Tool method to perform various transfer actions

        Args:
            action: Action to perform (get_accounts, create_intent, authorize, execute, status, list)

        Returns:
            Result data based on the action performed
        """
        
        try:
            valid_actions = ["get_accounts", "create_intent", "authorize", "execute", "status", "list"]
            if action not in valid_actions:
                raise ValueError(f"Invalid action. Must be one of: {valid_actions}")

            if action == "get_accounts":
                result = self._get_accounts()
            elif action == "create_intent":
                result = self._create_transfer_intent()
            elif action == "authorize":
                result = self._authorize_transfer()
            elif action == "execute":
                result = self._execute_transfer()
            elif action == "status":
                result = self._get_transfer_status()
            elif action == "list":
                result = self._list_transfers()
            else:
                raise ValueError(f"Unsupported action: {action}")

            return {
                "action": action,
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat(),
                "message": self.status
            }

        except Exception as e:
            error_msg = f"Failed to perform {action}: {str(e)}"
            self.status = error_msg
            return {
                "action": action,
                "status": "error",
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
            }

    def transfer(self) -> Data:
        """Transfer tool for agent"""
        
        tool_data = {
            "data": self.perform_transfer_action(self.action)
        }

        return Data(data=tool_data) 

import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.investments_transactions_get_request import InvestmentsTransactionsGetRequest
from datetime import datetime, timedelta

# Replace these with your Plaid Sandbox credentials
client_id = '6855e97df0e9500023f82d66'
secret = '3b05ca57d8ecee40065a1a33317e84'
# 1. Configure Plaid client for Sandbox
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': client_id,
        'secret': secret,
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# 2. Create a Link Token (including investments product)
# link_request = LinkTokenCreateRequest(
#     products=[Products('auth'), Products('transactions'), Products('investments')],
#     client_name="Plaid Test App",
#     country_codes=[CountryCode('US')],
#     language='en',
#     user={'client_user_id': 'user_good'}
# )
# link_response = client.link_token_create(link_request)
# link_token = link_response['link_token']
# print("Link token:", link_token)

# 3. Simulate public token creation (Sandbox only)
sandbox_public_token_response = client.sandbox_public_token_create({
    'institution_id': 'ins_109508',  # Use a valid sandbox institution that supports investments
    'initial_products': ['auth', 'transactions', 'investments'],
})
public_token = sandbox_public_token_response['public_token']
print("Public token:", public_token)

# 4. Exchange public token for access token
exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
exchange_response = client.item_public_token_exchange(exchange_request)
access_token = exchange_response['access_token']
print("Access token:", access_token)

# 5. Fetch account balances
balance_request = AccountsBalanceGetRequest(access_token=access_token)
balance_response = client.accounts_balance_get(balance_request)
print("Accounts and balances:", balance_response.to_dict())

# 6. Display all account details
accounts = balance_response['accounts']
investment_accounts = []

print("\n" + "="*60)
print("ALL ACCOUNTS SUMMARY")
print("="*60)

for account in accounts:
    print(f"Account: {account['name']}")
    print(f"  Type: {account['type']}")
    print(f"  Type (raw): {repr(account['type'])}")  # Debug: see exact type and value
    print(f"  Type class: {type(account['type'])}")  # Debug: see the Python type
    if 'subtype' in account and account['subtype']:
        print(f"  Subtype: {account['subtype']}")
    print(f"  Balance: {account['balances']['current']} {account['balances'].get('iso_currency_code', 'USD')}")
    
    # Track investment accounts for detailed holdings fetch
    # More robust comparison that handles different formats
    account_type_str = str(account['type']).lower()
    print(f"  Type as string: '{account_type_str}'")  # Debug: see string conversion
    
    if account_type_str == 'investment' or 'investment' in account_type_str:
        print("INVESTMENT ACCOUNT FOUND")
        investment_accounts.append(account)
    
    print()

# 7. Fetch and display investment holdings
if investment_accounts:
    print("\n" + "="*60)
    print("INVESTMENT HOLDINGS DETAILS")
    print("="*60)
    
    try:
        holdings_request = InvestmentsHoldingsGetRequest(access_token=access_token)
        holdings_response = client.investments_holdings_get(holdings_request)
        print("RESPONSE HOLDINGS")
        print(holdings_response)
        holdings = holdings_response['holdings']
        print(holdings)
        print("\n")
        securities = holdings_response['securities']
        accounts_data = holdings_response.get('accounts', [])
        
        # Create dictionaries for quick lookup
        securities_dict = {security['security_id']: security for security in securities}
        accounts_dict = {account['account_id']: account for account in accounts_data}
        
        print(f"Total Holdings Found: {len(holdings)}")
        print(f"Total Securities: {len(securities)}")
        print(f"Investment Accounts with Holdings: {len(accounts_data)}")
        print()
        
        if holdings:
            # Group holdings by account for better organization
            holdings_by_account = {}
            for holding in holdings:
                account_id = holding['account_id']
                if account_id not in holdings_by_account:
                    # Find account name from multiple sources
                    account_name = 'Unknown Account'
                    if account_id in accounts_dict:
                        account_name = accounts_dict[account_id].get('name', account_name)
                    else:
                        # Fallback to original accounts list
                        account_name = next((acc['name'] for acc in accounts if acc['account_id'] == account_id), account_name)
                    
                    holdings_by_account[account_id] = {
                        'name': account_name,
                        'holdings': []
                    }
                holdings_by_account[account_id]['holdings'].append(holding)
            
            # Display holdings by account
            for account_id, account_data in holdings_by_account.items():
                print(f"📈 {account_data['name']} (Account ID: {account_id})")
                print("-" * 50)
                
                total_value = 0
                total_cost_basis = 0
                holdings_count = len(account_data['holdings'])
                
                # Sort holdings by current value (largest first)
                sorted_holdings = sorted(account_data['holdings'], 
                                       key=lambda x: x['quantity'] * x.get('institution_price', 0), 
                                       reverse=True)
                
                for i, holding in enumerate(sorted_holdings, 1):
                    security_id = holding['security_id']
                    security = securities_dict.get(security_id, {})
                    
                    # Calculate values
                    quantity = holding['quantity']
                    institution_price = holding.get('institution_price', 0)
                    current_value = quantity * institution_price
                    total_value += current_value
                    
                    # Display holding details with position number
                    print(f"  #{i} 🏢 {security.get('name', 'Unknown Security')}")
                    
                    # Security details
                    if 'ticker_symbol' in security and security['ticker_symbol']:
                        print(f"     📊 Ticker: {security['ticker_symbol']}")
                    if 'type' in security:
                        print(f"     🏷️  Security Type: {security['type']}")
                    if 'cusip' in security and security['cusip']:
                        print(f"     🔢 CUSIP: {security['cusip']}")
                    
                    # Position details
                    print(f"     📦 Quantity: {quantity:,.4f}")
                    print(f"     💵 Price per Share: ${institution_price:.2f}")
                    print(f"     💰 Current Value: ${current_value:,.2f}")
                    
                    # Cost basis and performance
                    if 'cost_basis' in holding and holding['cost_basis']:
                        cost_basis = holding['cost_basis']
                        total_cost_basis += cost_basis
                        gain_loss = current_value - cost_basis
                        gain_loss_pct = ((current_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
                        
                        print(f"     📈 Cost Basis: ${cost_basis:,.2f}")
                        print(f"     {'📈' if gain_loss >= 0 else '📉'} Gain/Loss: ${gain_loss:,.2f} ({gain_loss_pct:+.2f}%)")
                        
                        # Portfolio weight
                        if total_value > 0:
                            weight = (current_value / total_value) * 100 if i == len(sorted_holdings) else 0
                            if weight > 0:
                                print(f"     🥧 Portfolio Weight: {weight:.1f}%")
                    
                    # Additional market data if available
                    if 'unofficial_currency_code' in holding and holding['unofficial_currency_code']:
                        print(f"     💱 Currency: {holding['unofficial_currency_code']}")
                    
                    # Holding metadata
                    if 'account_id' in holding:
                        print(f"     🏦 Account: ...{account_id[-8:]}")
                    
                    print()
                
                # Account summary
                print(f"  📊 Holdings Summary for {account_data['name']}:")
                print(f"     Total Positions: {holdings_count}")
                print(f"     💰 Total Market Value: ${total_value:,.2f}")
                if total_cost_basis > 0:
                    total_gain_loss = total_value - total_cost_basis
                    total_gain_loss_pct = (total_gain_loss / total_cost_basis) * 100
                    print(f"     📈 Total Cost Basis: ${total_cost_basis:,.2f}")
                    print(f"     {'📈' if total_gain_loss >= 0 else '📉'} Total Gain/Loss: ${total_gain_loss:,.2f} ({total_gain_loss_pct:+.2f}%)")
                print()
            
            # Overall portfolio summary
            overall_total = sum(holding['quantity'] * holding.get('institution_price', 0) for holding in holdings)
            overall_cost_basis = sum(holding.get('cost_basis', 0) for holding in holdings if holding.get('cost_basis'))
            
            print("="*60)
            print("🎯 COMPLETE INVESTMENT PORTFOLIO SUMMARY")
            print("="*60)
            print(f"Total Investment Accounts: {len(holdings_by_account)}")
            print(f"Total Holdings/Positions: {len(holdings)}")
            print(f"Total Unique Securities: {len(securities)}")
            print(f"💰 Total Portfolio Value: ${overall_total:,.2f}")
            
            if overall_cost_basis > 0:
                overall_gain_loss = overall_total - overall_cost_basis
                overall_gain_loss_pct = (overall_gain_loss / overall_cost_basis) * 100
                print(f"📈 Total Cost Basis: ${overall_cost_basis:,.2f}")
                print(f"{'📈' if overall_gain_loss >= 0 else '📉'} Total Portfolio Gain/Loss: ${overall_gain_loss:,.2f} ({overall_gain_loss_pct:+.2f}%)")
            
            # Security type breakdown
            security_types = {}
            for holding in holdings:
                security = securities_dict.get(holding['security_id'], {})
                sec_type = security.get('type', 'Unknown')
                value = holding['quantity'] * holding.get('institution_price', 0)
                security_types[sec_type] = security_types.get(sec_type, 0) + value
            
            if security_types:
                print(f"\n🏷️  Portfolio Breakdown by Security Type:")
                for sec_type, value in sorted(security_types.items(), key=lambda x: x[1], reverse=True):
                    percentage = (value / overall_total * 100) if overall_total > 0 else 0
                    print(f"     {sec_type}: ${value:,.2f} ({percentage:.1f}%)")
            
            print("="*60)
            
        else:
            print("❌ No holdings found in investment accounts.")
            print("\nThis could mean:")
            print("1. The investment accounts exist but have no current positions")
            print("2. All positions may have been sold/closed")
            print("3. The sandbox data may not include holdings information")
        
    except Exception as e:
        print(f"❌ Error fetching investment holdings: {e}")
        print("\nThis error might be due to:")
        print("1. The sandbox institution doesn't have investment holdings data")
        print("2. The investments product isn't properly enabled")
        print("3. API configuration or authentication issues")
        print("4. The investment accounts may not be properly set up")
        print(f"\nDetailed error: {str(e)}")

else:
    print("\n" + "="*60)
    print("NO INVESTMENT ACCOUNTS FOUND")
    print("="*60)
    print("This sandbox institution may not have investment accounts,")
    print("or they may not be enabled for this test user.")

# # 8. Fetch and display investment transactions
# print("\n" + "="*60)
# print("INVESTMENT TRANSACTIONS")
# print("="*60)

# try:
#     # Set date range for transactions (last 30 days)
#     start_date = datetime.now().date() - timedelta(days=30)
#     end_date = datetime.now().date()
    
#     transactions_request = InvestmentsTransactionsGetRequest(
#         access_token=access_token,
#         start_date=start_date,
#         end_date=end_date
#     )
#     transactions_response = client.investments_transactions_get(transactions_request)
    
#     transactions = transactions_response['investment_transactions']
#     securities = transactions_response.get('securities', [])
    
#     # Create a dictionary for quick security lookup
#     securities_dict = {security['security_id']: security for security in securities}
    
#     print(f"Total Investment Transactions Found: {len(transactions)}")
#     print(f"Date Range: {start_date} to {end_date}")
#     print()
    
#     if transactions:
#         # Group transactions by account for better organization
#         transactions_by_account = {}
#         for transaction in transactions:
#             account_id = transaction['account_id']
#             if account_id not in transactions_by_account:
#                 # Find account name
#                 account_name = next((acc['name'] for acc in accounts if acc['account_id'] == account_id), 'Unknown Account')
#                 transactions_by_account[account_id] = {
#                     'name': account_name,
#                     'transactions': []
#                 }
#             transactions_by_account[account_id]['transactions'].append(transaction)
        
#         # Display transactions by account
#         for account_id, account_data in transactions_by_account.items():
#             print(f"📊 {account_data['name']} (Account ID: {account_id})")
#             print("-" * 50)
            
#             # Sort transactions by date (most recent first)
#             sorted_transactions = sorted(account_data['transactions'], 
#                                        key=lambda x: x['date'], reverse=True)
            
#             for transaction in sorted_transactions:
#                 security_id = transaction.get('security_id')
#                 security = securities_dict.get(security_id, {}) if security_id else {}
                
#                 # Display transaction details
#                 print(f"  📅 Date: {transaction['date']}")
#                 print(f"  💼 Type: {transaction['type']}")
#                 if 'subtype' in transaction and transaction['subtype']:
#                     print(f"  🏷️  Subtype: {transaction['subtype']}")
                
#                 # Security information
#                 if security:
#                     print(f"  🏢 Security: {security.get('name', 'Unknown')}")
#                     if 'ticker_symbol' in security and security['ticker_symbol']:
#                         print(f"     Ticker: {security['ticker_symbol']}")
                
#                 # Quantity and price information
#                 if 'quantity' in transaction and transaction['quantity']:
#                     print(f"  📈 Quantity: {transaction['quantity']}")
                
#                 if 'price' in transaction and transaction['price']:
#                     print(f"  💵 Price: ${transaction['price']:.2f}")
                
#                 if 'amount' in transaction and transaction['amount']:
#                     print(f"  💰 Amount: ${transaction['amount']:.2f}")
                
#                 # Additional details
#                 if 'fees' in transaction and transaction['fees']:
#                     print(f"  💸 Fees: ${transaction['fees']:.2f}")
                
#                 if 'description' in transaction and transaction['description']:
#                     print(f"  📝 Description: {transaction['description']}")
                
#                 print()
        
#         # Summary statistics
#         total_transactions = len(transactions)
#         transaction_types = {}
#         total_amount = 0
        
#         for transaction in transactions:
#             trans_type = transaction['type']
#             transaction_types[trans_type] = transaction_types.get(trans_type, 0) + 1
#             if 'amount' in transaction and transaction['amount']:
#                 total_amount += transaction['amount']
        
#         print("="*60)
#         print("📈 INVESTMENT TRANSACTIONS SUMMARY")
#         print("="*60)
#         print(f"Total Transactions: {total_transactions}")
#         print(f"Total Transaction Amount: ${total_amount:.2f}")
#         print("\nTransaction Types:")
#         for trans_type, count in transaction_types.items():
#             print(f"  {trans_type}: {count}")
#         print("="*60)
        
#     else:
#         print("❌ No investment transactions found in the specified date range.")
#         print("\nThis could be because:")
#         print("1. The sandbox account has no investment transaction history")
#         print("2. No transactions occurred in the last 30 days")
#         print("3. The investment transactions feature may not be properly configured")
#         print("\n💡 Tips to troubleshoot:")
#         print("- Try extending the date range")
#         print("- Check if the sandbox institution supports investment transactions")
#         print("- Verify that the 'investments' product is properly enabled")
#         print("- Consider using a different sandbox institution (ins_109508 used above)")

# except Exception as e:
#     print(f"❌ Error fetching investment transactions: {e}")
#     print("\nThis error might be due to:")
#     print("1. The investments product not being properly enabled")
#     print("2. API configuration issues")
#     print("3. The sandbox institution not supporting investment transactions")
#     print("4. Date range issues or other API parameter problems")
#     print(f"\nDetailed error: {str(e)}")



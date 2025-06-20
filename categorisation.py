import json

def get_relevant_news_categories(user_data_json, user_statement):
    """
    Select relevant news categories based on user financial data and statement.

    :param user_data_json: JSON string with keys like 'accounts', 'credit_cards', 'loans', 'investments', etc.
    :param user_statement: str, user's stated goals/interests
    :return: JSON string with a list of relevant news category codes (sorted by relevance)

    Example:
        user_data_json = json.dumps({
            'accounts': [
                {'type': 'investment'},
                {'type': 'bank'},
                {'type': 'crypto'},
                {'type': 'retirement'},
                {'type': 'real_estate'},
                {'type': 'energy'},
                {'type': 'manufacturing'},
                {'type': 'retail'},
                {'type': 'life_sciences'}
            ],
            'credit_cards': [{'issuer': 'Chase'}],
            'loans': [
                {'type': 'student_loan'},
                {'type': 'mortgage'},
                {'type': 'loan'}
            ],
            'investments': [
                {'type': 'stock'},
                {'type': 'crypto'},
                {'type': 'etf'}
            ]
        })
        user_statement = (
            "I'm interested in crypto, tech, biotech, energy, retail, and manufacturing. "
            "I want to pay off my student loans, mortgage, and save for retirement and a house."
        )

        result_json = get_relevant_news_categories(user_data_json, user_statement)
        # result_json will be:
        # {
        #   "relevant_categories": [
        #     "economy_fiscal",
        #     "real_estate",
        #     "earnings",
        #     "ipo",
        #     "mergers_and_acquisitions",
        #     "financial_markets",
        #     "technology",
        #     "blockchain",
        #     "economy_monetary",
        #     "finance",
        #     "economy_macro",
        #     "energy_transportation",
        #     "manufacturing",
        #     "retail_wholesale",
        #     "life_sciences"
        #   ]
        # }
    """

    # Parse input JSON
    user_data = json.loads(user_data_json)

    # News categories mapping
    categories = {
        'blockchain': 'Blockchain',
        'earnings': 'Earnings',
        'ipo': 'IPO',
        'mergers_and_acquisitions': 'Mergers & Acquisitions',
        'financial_markets': 'Financial Markets',
        'economy_fiscal': 'Economy - Fiscal Policy',
        'economy_monetary': 'Economy - Monetary Policy',
        'economy_macro': 'Economy - Macro/Overall',
        'energy_transportation': 'Energy & Transportation',
        'finance': 'Finance',
        'life_sciences': 'Life Sciences',
        'manufacturing': 'Manufacturing',
        'real_estate': 'Real Estate & Construction',
        'retail_wholesale': 'Retail & Wholesale',
        'technology': 'Technology'
    }

    # Initialize a set for relevant categories
    relevant = set()

    # Map account types to news categories
    account_type_map = {
        'crypto': ['blockchain'],
        'investment': ['earnings', 'ipo', 'mergers_and_acquisitions', 'financial_markets', 'technology'],
        'retirement': ['economy_macro', 'economy_monetary', 'financial_markets'],
        'credit_card': ['economy_monetary', 'finance'],
        'loan': ['economy_fiscal', 'finance'],
        'mortgage': ['real_estate', 'economy_monetary'],
        'student_loan': ['economy_fiscal', 'finance'],
        'bank': ['finance', 'economy_macro'],
        'real_estate': ['real_estate'],
        'energy': ['energy_transportation'],
        'manufacturing': ['manufacturing'],
        'retail': ['retail_wholesale'],
        'life_sciences': ['life_sciences'],
    }

    # Analyze user's accounts
    accounts = user_data.get('accounts', [])
    for account in accounts:
        acct_type = account.get('type', '').lower()
        for key, cats in account_type_map.items():
            if key in acct_type:
                relevant.update(cats)

    # Analyze user's credit cards
    if user_data.get('credit_cards'):
        relevant.update(['economy_monetary', 'finance'])

    # Analyze user's loans
    for loan in user_data.get('loans', []):
        loan_type = loan.get('type', '').lower()
        if 'student' in loan_type:
            relevant.update(['economy_fiscal', 'finance'])
        if 'mortgage' in loan_type:
            relevant.update(['real_estate', 'economy_monetary'])
        else:
            relevant.update(['finance', 'economy_fiscal'])

    # Analyze user's investments
    for inv in user_data.get('investments', []):
        inv_type = inv.get('type', '').lower()
        if 'crypto' in inv_type:
            relevant.add('blockchain')
        if 'stock' in inv_type or 'etf' in inv_type:
            relevant.update(['earnings', 'ipo', 'mergers_and_acquisitions', 'financial_markets', 'technology'])

    # Analyze user statement for keywords
    statement = user_statement.lower()
    keyword_map = {
        'crypto': 'blockchain',
        'bitcoin': 'blockchain',
        'ethereum': 'blockchain',
        'stock': 'financial_markets',
        'invest': 'financial_markets',
        'retire': 'economy_macro',
        'mortgage': 'real_estate',
        'house': 'real_estate',
        'home': 'real_estate',
        'loan': 'finance',
        'debt': 'finance',
        'save': 'economy_monetary',
        'interest rate': 'economy_monetary',
        'inflation': 'economy_monetary',
        'tax': 'economy_fiscal',
        'job': 'economy_macro',
        'energy': 'energy_transportation',
        'tech': 'technology',
        'manufacturing': 'manufacturing',
        'retail': 'retail_wholesale',
        'biotech': 'life_sciences',
        'health': 'life_sciences'
    }
    for keyword, cat in keyword_map.items():
        if keyword in statement:
            relevant.add(cat)

    # Always include economy_macro as a baseline
    relevant.add('economy_macro')

    # Prioritize categories (example: most relevant first)
    priority_order = [
        'student_loan', 'mortgage', 'investment', 'crypto', 'credit_card', 'loan', 'bank'
    ]
    prioritized = []
    for key in priority_order:
        for cat in account_type_map.get(key, []):
            if cat in relevant:
                prioritized.append(cat)
    # Add the rest, preserving order
    for cat in categories:
        if cat not in prioritized and cat in relevant:
            prioritized.append(cat)

    return json.dumps({"relevant_categories": prioritized})

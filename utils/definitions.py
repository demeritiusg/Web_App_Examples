QBO_REVENUE_ACCOUNTS = {
    'Oil Sales - Working Interest': '4000',
    'Oil Sales - Royalty Interest': '4010',
    'Gas Sales - Working Interest': '4100',
    'Gas Sales - Royalty Interest': '4110',
    'Product Sales - Royalty': '4210',
    'Miscellaneous Royalty Income': '4400'
}

QBO_EXPENSE_ACCOUNTS = {
    'Production Tax - Working': '5000',
    'Production Tax - Royalty': '5001',
    'State Backup W/H - NM': '5010',
    'State Backup W/H - OK': '5015',
    'State Backup W/H - CA': '5020',
    'State Backup W/H - MT': '5025',
    'State Backup W/H - ND': '5030',
    'State Backup W/H - UT': '5035',
    'State Backup W/H - WY': '5040',
    'State Backup W/H - CO': '5045',
    'State Backup W/H - PA': '5050',
    'State Withholding Tax - Unallocated': '5091',
    'Other Oil & Gas Expenses:Marketing Expense (W)': '5120',
    'Other Oil & Gas Expenses:Marketing Expense (R)': '5121',
    'Other Oil & Gas Expenses:Other Expense - Royalty': '5331',
    'Other Oil & Gas Expenses:Reimbursements to Prior Owners': '5350',
    'Other Oil & Gas Expenses:Lease Operating Expense': '5400',
    'Lease Operating Expense': '5400'
}

QBO_COMPANY_DOMAINS = {
    'WIRC': 'https://c2.qbo.intuit.com',
    'CYPT': 'https://c3.qbo.intuit.com',
    'LTD': 'https://c3.qbo.intuit.com',
    'LLC': 'https://c3.qbo.intuit.com',
    'RCP': 'https://c3.qbo.intuit.com',
    'MILL': 'https://c3.qbo.intuit.com',
    'FOOT': 'https://c6.qbo.intuit.com',
    'SUN': 'https://c71.qbo.intuit.com',
    'RSM': 'https://c43.qbo.intuit.com',
    'SHR': 'https://c41.qbo.intuit.com',
}

QBO_COMPANIES = {
    'production':
        ['RCM', 'RCP', 'CYPT', 'FOOT', 'LLC', 'LTD',
         'MILL', 'WIRC', 'MIRH', 'SUN', 'RSM', 'SHR']}


redirect_uri = "https://rc.royaltyclearinghouse.com/home/call-back"
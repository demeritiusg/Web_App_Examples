import os
import csv
import json
import urllib.parse
import decimal as dec
from pprint import pprint
from collections import defaultdict

from io import StringIO
from datetime import date, datetime
from configparser import ConfigParser
from multiprocessing.pool import ThreadPool
from functools import partial

import arrow
import requests
from frozendict import frozendict

# from rc_code.helpers import unique_filename
from utils import definitions, rc_helpers


from settings import BASE_DIR
from utils.rc_helpers import to_xl_tmp

RC_QBO_Exception = 'Pass'


"""
This is probaly useless

"""


class TokensExpired(RC_QBO_Exception):
    pass


class UnknownError(RC_QBO_Exception):
    pass


class InvalidReconnectRequest(RC_QBO_Exception):
    pass


class XMLError(RC_QBO_Exception):
    pass


class NoSecretsFile(RC_QBO_Exception):
    pass


class RequestFailed(RC_QBO_Exception):
    pass


class PostFailed(RC_QBO_Exception):
    pass


class RefreshFailed(RC_QBO_Exception):
    pass


class AccountDoesNotExist(RC_QBO_Exception):
    pass


class PurchaserDoesNotExist(RC_QBO_Exception):
    pass


class ParseError(RC_QBO_Exception):
    pass


class RefreshOutOfWindow(RC_QBO_Exception):
    pass


class InvalidCompany(RC_QBO_Exception):
    pass


batch_dict = frozendict({
    # The limit of the number of operations that can be submitted to the QBO batch
    # endpoint at once as specified by QuickBooks.
    'batch_item_limit': 30,
    # The maximum number of results that can be returned from an endpoint as specified
    # by QuickBooks.
    'max_results': 1000
})

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, dec.Decimal):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def json_dumps(data):
    return json.dumps(data, cls=CustomJSONEncoder)


def to_customer_url(entity, id):
    domain = definitions.QBO_COMPANY_DOMAINS[entity]
    url = '{}/app/customerdetail?nameId={}'.format(domain, id)
    return url


class QBO_API:
    """A wrapper to make resource requests to the QuickBooks Online API using the OAuth access
    tokens that were acquired previously via the process decribed here:

        https://github.com/IntuitDeveloper/oauth-python

    A reconnect request will be sent with `self.refresh_access_tokens`. When a valid response is
    returned, which will be between 5 and 6 months from the AccessDate in the `self.secrets_file`,
    the AccessDate, AccessKey, and AccessSecret values will be updated.
    """

    def __repr__(self):
        env = self.env_type
        companies = ' '.join(self.companies)
        return '<QBO . {} . {}>'.format(env, companies)

    def init_company(self, company):

        c = company

        # TOKENS_FILE = f'{BASE_DIR}/tokens/tockens.cfg'
        # token_config = ConfigParser()
        # token_config.read(TOKENS_FILE)

        # stoken = token_config[c]['access_token']
        # realm_id = token_config[c]['realm_id']

        base_resource_url = self.QBO_BASE_URL.format(accounting_url=self.config['APP']['accounting_url'])

        # oauth = 'Bearer ' + stoken

        return realm_id, oauth

    def retrieve_account_ids(self, company, fully_qualified_names, use_cache=True):
        # Review Allocations
        """Retrieve the QBO Accounts for `company` with `fully_qualified_names`.

        Parameters
        ----------
        company : str
            One of `QBO_API.companies`.

        fully_qualified_names : List[str]
            The names of the QBO accounts to retrieve.

        Returns
        -------
        return : dict
            { account_name: str
            , account_id: int
            }
        """
        assert company in self.companies

        accounts = {}
        # If all accounts are already cached, then just return the cached values.
        if use_cache:
            company_accounts = set(self._cache_company_accounts[company])
            if len(set(fully_qualified_names) - company_accounts) == 0:
                for account in fully_qualified_names:
                    accounts[account] = self._cache_company_accounts[company][account]

                return accounts

        account_names = ', '.join([
            "'%s'" % x
            for x in fully_qualified_names])
        # account_names = "', '".join([repr(x) for x in fully_qualified_names])
        sql = "SELECT Id, FullyQualifiedName FROM Account WHERE FullyQualifiedName IN ({})".format(account_names)
        # quoted_sql = urllib.parse.quote(sql)
        # resource_url = "query?query=" + quoted_sql

        # sql = "SELECT Id, FullyQualifiedName FROM Account " \
        #       f"WHERE FullyQualifiedName IN ({account_names})"
        quoted_sql = urllib.parse.quote(sql)
        resource_url = 'query?query={}'.format(quoted_sql)

        response = self.request_resource(company, resource_url)
        if response['QueryResponse']:
            for account in response['QueryResponse']['Account']:
                account_id = account['Id']
                account_name = account['FullyQualifiedName']
                accounts[account_name] = account_id

        accounts_exist = list(map(lambda x: x in accounts, fully_qualified_names))
        if False in accounts_exist:
            missing = fully_qualified_names[accounts_exist.index(False)]
            # missing = account_names
            raise AccountDoesNotExist(
                "The account <{}> does not exist in QBO for company {}.".format(missing, company)
            )

        self._cache_company_accounts[company].update(accounts)
        return accounts

    def create_purchasers(self, company, purchasers):
        """Create QBO Customer module records for purchasers.

        Parameters
        ----------
        company : str
            One of `QBO_API.companies` to create the purchasers within.

        purchasers : List[dict]
            Purchaser records from `read_purchasers_csv`.

        Returns
        -------
        return : (Exception, QBO Batch Response, `purchasers`)
            The return from `QBO_API.create_resources`.
        """
        assert company in self.companies

        # Retrieve existing purchasers.
        qbo_purchasers = [
            (p['purchaser_name'], p['purchaser_code'])
            for p in self.retrieve_purchasers(company)
        ]
        if qbo_purchasers:
            qbo_purch_names, qbo_purch_codes = zip(*qbo_purchasers)
        else:
            qbo_purch_names = []
            qbo_purch_codes = []

        # Ensure the purchasers don't already exist in the company.
        for p in purchasers:
            # Check for existing purchaser codes.
            if p['PurchaserCode'] in qbo_purch_codes:
                resp = input(
                    "Purchaser code {p['PurchaserCode']} already exists in {}.\n\nSkip? [yN]: ".format(company))
                if resp in 'yY':
                    p['__skip__'] = True
                else:
                    raise Exception("User aborted.")
            else:
                p['__skip__'] = False

            # Check for existing purchaser names.
            if p['PurchaserName'] in qbo_purch_names:
                resp = input(
                    "Purchaser name {p['PurchaserName']} already exists in {}.\n\nSkip? [yN]: ".format(company))
                if resp in 'yY':
                    p['__skip__'] = True
                else:
                    raise Exception("User aborted.")
            else:
                p['__skip__'] = False

        # Convert the purchasers that we didn't skip into Customer JSON.
        customers = [purchaser_to_customer(p) for p in purchasers if not p['__skip__']]

        return self.create_resources(
            company=company,
            resource_name='Customer',
            resources=customers
        )

    def create_purchaser_deposits(self, company, deposits):
        """Create deposits from purchaser checks which will be placed
        into the purchaser clearing account specified in config['purchaser_clearing_account_ref'].

        Parameters
        ----------
        company : str
            One of `QBO_API.companies` to create deposits for.

        deposits : List[dict]
            The list of deposits to create. The purchaser code will be
            checked against existing `Customer`s in QBO, which is
            where the purchasers are reflected.
                [{ 'purchaser_name': str,
                   'purchaser_code': str,
                   'amount': decimal
                }]

        Returns
        -------
        return : batch_responses
            The batch responses from `QBO_API.create_resources`. If any faults are return or an
            exception is raised in the batch process, then `handle_batch_failure` will exit into
            a PDB session.
        """
        assert company in self.companies

        qbo_accounts = {
            key: {'name': key, 'value': val}
            for key, val in self.retrieve_account_ids(
                company=company,
                fully_qualified_names=['Purchaser Clearing Account', 'Checking - Texas Capital Bank']
            ).items()
        }
        qbo_purchasers = {
            x['purchaser_code']: x
            for x in self.retrieve_purchasers(company)
        }
        # Validate that all purchasers in the deposits exist before proceeding.
        missing_purchasers = []
        for deposit in deposits:
            if deposit['purchaser_code'] not in qbo_purchasers:
                missing_purchasers.append(
                    '%s %s' % (deposit['purchaser_code'], deposit['purchaser_name'])
                )
        if missing_purchasers:
            missing_purchasers_text = '\n'.join(missing_purchasers)
            raise Exception(
                "Ensure the following purchasers exist in QBO "
                "before creating deposits:\n\n{}".format(missing_purchasers_text))

        deposit_creation_resources = []
        for deposit in deposits:
            purchaser = qbo_purchasers[deposit['purchaser_code']]
            entity = {
                'value': purchaser['id'],
                'name': purchaser['purchaser_name'],
                'type': 'CUSTOMER'
            }
            deposit_creation_json = {
                'DepositToAccountRef': qbo_accounts['Checking - Texas Capital Bank'],
                'TotalAmt': deposit['amount'],
                'PrivateNote': deposit['reference'],
                'Line': [{
                    'Amount': deposit['amount'],
                    'DetailType': 'DepositLineDetail',
                    'DepositLineDetail': {
                        'Entity': entity,
                        'AccountRef': qbo_accounts[r'Purchaser Clearing Account']
                    }
                }]
            }
            deposit_creation_resources.append(deposit_creation_json)

        return self.create_resources(
            company=company,
            resource_name='Deposit',
            resources=deposit_creation_resources
        )

    def retrieve_purchasers(self, company):
        """Return a list of customers from the Customer table. Purchasers are
        mapped to a Customer in QBO, and the CompanyName field will be the CDEX
        purchaser code. This routine is primarily used to map the purchaser name
        to the purchaser code for the purchaser clearing utility.

        Parameters
        ----------
        company : str
            One of `QBO_API.companies'.

        Returns
        -------
        return : List[dict]
            [{id: str, purchaser_name: str, purchaser_code: str}]
        """
        assert company in self.companies

        query = r"SELECT Id, CompanyName, DisplayName FROM Customer"

        purchasers = []
        json_response = self.request_query_resource(company, 'Customer', query)
        for record in parse_customers(json_response):
            purchasers.append({
                'id': record['id'],
                'purchaser_name': record['display_name'],
                'purchaser_code': record['company_name'],
                'purchaser_url': to_customer_url(entity=company, id=record['id'])
            })
        return purchasers

    def _txn_date_range_as_where(self, month):
        start = arrow.get(month).format('YYYY-MM-DD')
        end = arrow.get(month).replace(months=+1).format('YYYY-MM-DD')
        sql = "WHERE TxnDate >= '{}' AND TxnDate < '{}'".format(start, end)
        return sql

    def retrieve_deposits(self, company, check_month):
        """Return all deposits to the 4150 - Purchaser Clearing account within
        the specified `check_month`.

        !! WARNING !!

        There's a bug in either `requests` or `oauthlib` that does not properly escape single quotes.
        I created the following issue regarding the problem:

        https://github.com/requests/requests-oauthlib/issues/298

        Manually patching `oauthlib` by adding an apostrophe to the set in the following line seems
        to fix the issue:

        https://github.com/idan/oauthlib/blob/cfb82feb03fcd60b3b66ac09bf1b478cd5f11b7d/oauthlib/common.py#L112

        Parameters
        ----------
        company : str
           A company in `QBO_API.companies`.

        check_month : str
            The month to filter the `Deposit.TxnDate` by in the form YYYY-MM.

        Returns
        -------
        return : List[dict]
            [{company: str, purchaser_code: str | `parse_purchaser_clearing_deposits`}]
        """
        assert company in self.companies

        qbo_purchasers = {
            x['purchaser_name']: x['purchaser_code']
            for x in self.retrieve_purchasers(company)
        }
        qbo_accounts = self.retrieve_account_ids(
            company=company,
            fully_qualified_names=['Purchaser Clearing Account']
        )
        where_txn_range = self._txn_date_range_as_where(check_month)
        sql = "SELECT * FROM Deposit {}".format(where_txn_range)
        resource_url = "query?query={}".format(sql)

        deposits = []
        json_response = self.request_resource(company, resource_url)
        purchaser_clearing_id = qbo_accounts['Purchaser Clearing Account']
        for deposit in parse_purchaser_clearing_deposits(json_response, purchaser_clearing_id):
            deposit['purchaser_code'] = qbo_purchasers.get(deposit['purchaser'], None)
            deposits.append(deposit)

        return deposits

    def retrieve_journal_entries(self, companies, txn_month=None, account_id=None):
        """Return a list of dictionaries of the JournalEntry table.

        Parameters
        ----------
        companies : List[str]
            The list of `self.QBO_COMPANIES` to retrieve the journal entries for.

        Returns
        -------
        return : List[dict]
            [{ company: str | `parse_journal_entries`}]
        """
        if txn_month:
            where_txn_range = self._txn_date_range_as_where(txn_month)
            sql = "SELECT * FROM JournalEntry {}".format(where_txn_range)
            resource = "query?query={}".format(sql)
        else:
            resource = "query?query=SELECT * FROM JournalEntry"

        journal_entries = []
        for company, json_response in self.request_resource_companies(companies, resource):
            for journal_entry in parse_journal_entries(json_response, account_id):
                journal_entry['company'] = company
                journal_entries.append(journal_entry)

        return journal_entries

    def retrieve_purchaser_clearing_checks(self, company, check_month):
        """Companies with Working Interests will have Checks (Purchases) with a
        revenue portion that is entered into the 4150 Purchaser Clearing account.
        """
        where_txn_range = self._txn_date_range_as_where(check_month)
        sql = "SELECT * FROM Purchase {}".format(where_txn_range)
        resource = "query?query={}".format(sql)

        qbo_accounts = self.retrieve_account_ids(
            company=company,
            fully_qualified_names=['Purchaser Clearing Account']
        )
        purchaser_clearing_id = qbo_accounts['Purchaser Clearing Account']

        json_response = self.request_resource(company, resource, floats_as_decimals=True)
        checks = list(parse_purchaser_clearing_checks(json_response, purchaser_clearing_id))
        return checks

    def retrieve_general_ledger(self, companies, start_date, end_date, accounting_method):
        """Return a list of dictionaries of the GeneralLedger report.

        Parameters
        ----------

        companies : List[str]
            The list of `QBO_COMPANIES` to export the general ledger for.

        start_date : str
            An ISO date for the first date of the period.

        end_date : str
            An ISO date for the last date of the period.

        accounting_method : str
            Also called the Report Basis, either 'Cash' or 'Accrual'.

        Returns
        -------
        return : List[dict]
            [{ company: str | `parse_general_ledger` }]
        """
        assert accounting_method in ('Cash', 'Accrual')

        resource = "reports/GeneralLedger?start_date={}&end_date={}&accounting_method={}&minorversion=3".format(
            start_date, end_date, accounting_method)

        general_ledgers = []
        for company, json_response in self.request_resource_companies(companies, resource):
            for general_ledger in parse_general_ledger(json_response):
                general_ledger['company'] = company
                general_ledgers.append(general_ledger)

        return general_ledgers

    def export_general_ledger(self, companies, start_date, end_date, accounting_method, output_file):
        """Export the general ledgers to a CSV at `output_file` for each company in `companies`.

        See `QBO_API.retrieve_general_ledger` for other parameter definitions.

        Parameters
        ----------
        companies : List[str]
            The list of `QBO_COMPANIES` to export the general ledger data for.

        output_file : str
            The path to the CSV file to create.

        Returns
        -------
        return : None
            Creates the CSV `output_file` containing the general ledgers with a header.
        """
        general_ledgers = self.retrieve_general_ledger(companies, start_date, end_date, accounting_method)
        with open(output_file, 'w') as out:
            csv_writer = csv.writer(out, lineterminator='\n', delimiter='\t')
            header = general_ledgers[0].keys()
            csv_writer.writerow(header)
            csv_writer.writerows([x.values() for x in general_ledgers])

    def export_journal_entries(self, companies, output_file, txn_months=None):
        """Export the journal entries to a CSV at `output_file` for each company in `companies`.

        Parameters
        ----------
        companies : list of str
            The list of `QBO_COMPANIES` to export the journal entries for.

        output_file : str
            The path to the CSV file to create.

        Returns
        -------
        return : None
            Creates the CSV `output_file` with a header containing the journal entries.
        """
        with open(output_file, 'w') as out:
            csv_writer = csv.writer(out, lineterminator='\n')

            first = True
            for txn_month in txn_months:
                journal_entries = self.retrieve_journal_entries(companies, txn_month)
                if first:
                    header = journal_entries[0].keys()
                    csv_writer.writerow(header)
                    first = False

                rows = [e.values() for e in journal_entries]
                csv_writer.writerows(rows)

    def request_resource_companies(self, companies, resource_url):
        """Request `resource_url` for each company in `companies` using a ThreadPool.

        Parameters
        ----------
        companies : List[str]
            A set of `QBO_API.companies`.

        resource_url : str
            The trailing resource portion of the URL after the API prefix.

        Yields
        ------
        return : (company, `QBO_API.request_resource`)
        """
        with ThreadPool(len(companies)) as p:
            request_resource = partial(self.request_resource, resource_url=resource_url)
            results = p.map(request_resource, companies)
            for i, result in enumerate(results):
                yield companies[i], result

    def request_resource(self, company, resource_url, floats_as_decimals=False):
        """Request the source for `company` at `resource_url` with `self.config`.

        Parameters
        ----------
        company : str
            One of `QBO_API.companies`.

        resource_url : str
            The QBO title-cased resource following the API base url.

        Returns
        -------
        return : dict
            The JSON response from the QBO endpoint.
        """
        assert company in self.companies

        realm_id, oauth = self.init_company(company)

        response = request_resource(
            realm_id,
            oauth,
            resource_url,
            floats_as_decimals
        )
        return response

    def request_query_resource(self, company, resource_url, query):
        """Request the source for `company` at `resource_url` with `self.config`.

        Parameters
        ----------
        ----------
        company : str
            One of `QBO_API.companies`.

        resource_url : str
            The QBO title-cased resource following the API base url.

        Returns
        -------
        return : dict
            The JSON response from the QBO endpoint.
        """
        assert company in self.companies

        realm_id, oauth = self.init_company(company)
        response = request_query_resource(
            realm_id,
            oauth,
            resource_url,
            query,
            debug=self.debug
        )
        return response

    def create_resource(self, company, resource_url, resource, dry_run=False, **kwargs):
        """Create the resource at `resource_url` within `company`.

        Parameters
        ----------
        company : str
            One of `QBO_API.companies`.

        resource_url : str
            The title-cased name of a QBO API resource, such as: Customer.

        resource : dict
            The QBO resource to create.

        dry_run : bool = False
            Print the POST parameters instead of actually sending the request.

        Returns
        -------
        return : dict
            The JSON response from the QBO endpoint.
        """
        if company not in self.companies:
            raise InvalidCompany("<{}> is not an existing company.".format(company))

        realm_id, oauth = self.init_company(company)
        response = create_resource(
            realm_id,
            oauth,
            resource_url,
            resource,
            dry_run,
            **kwargs
        )
        return response

    def create_resources(self, company, resource_name, resources):
        """Create the resources for `resource_name` within `company` using the QBO batch API. See
        `create_resources` for additional parameter information.

        Parameters
        ----------
        company : str
            One of `QBO_API.companies`.

        resource_name : str
            The title-cased name of a QBO API resource, such as: Customer.

        resources : List[dict]
            The list of QBO resources to create.

        Returns
        -------
        return : (Exception, QBO Batch Response, `resources`)
            The return value from `create_resources`.
        """
        assert company in self.companies

        realm_id, oauth = self.init_company(company)
        return create_resources(
            realm_id,
            oauth,
            resource_name,
            resources
        )

    def retrieve_chart_of_accounts(self, companies=None):
        """Retrieve the list of accounts from all `companies`.

        Parameters
        ----------

        companies : List[str]
            A set of companies from `QBO_API.companies`.

        Returns
        -------
        return : List[(str, str str, str, str)]
            [ ( Company
              , AcctNum
              , FullyQualifiedName
              , AccountType
              , AccountSubType
              )
            , ...
            ]
        """
        _companies = companies or self.companies
        assert (set(_companies) - set(self.companies)) == set()

        resource_url = urllib.parse.quote("query?query=SELECT * FROM Account")
        chart_of_accounts = []
        for company, response in self.request_resource_companies(_companies, resource_url):
            for account in response['QueryResponse']['Account']:
                chart_of_accounts.append((company, account.get('AcctNum', ''), account['FullyQualifiedName'],
                                          account['AccountType'], account['AccountSubType']))
        return _companies, chart_of_accounts

    def export_chart_of_accounts(self, companies=None):
        """Generate a matrix for each account showing which companies the
        account exists within.

        Parameters
        ----------
        companies : List[str]
            A set of companies from `QBO_API.companies`.

        Returns
        -------
        return : None
            Opens a temporary Excel file containing the data.
        """
        companies, chart_of_accounts = self.retrieve_chart_of_accounts(companies)
        coa_matrix = chart_of_accounts_to_matrix(companies, chart_of_accounts)

        sheet_header = ['Account', 'Type', 'Detail Type'] + companies
        sorted_sheet = sorted(coa_matrix, key=lambda x: x[0])
        to_xl_tmp([sheet_header] + sorted_sheet, header=True)

    # def handle_refresh_response(self, company, response_xml):
    #     """The reconnect endpoint responses are described here:
    #
    #         https://developer.intuit.com/docs/0100_quickbooks_online/0100_essentials/000500_authentication_and_authorization/oauth_management_api#/Reconnect
    #
    #     If the request is within the refresh window, then the new access tokens will be written
    #     to the `self.secrets_file` in place of the old tokens.
    #
    #
    #     Parameters
    #     ----------
    #     company : str
    #         One of `QBO_API.companies` to handle the refresh for.
    #
    #     response_xml : str
    #         The XML response from the QBO refresh endpoint.
    #
    #
    #     Returns
    #     -------
    #     return : True
    #         Writes `QBO_API.config` to `QBO_API.secrets_file` with the new access tokens if the XML could be
    #         successfully parsed, otherwise various exceptions will be raised.
    #
    #
    #     Raises
    #     ------
    #     RefreshOutOfWindow
    #         QBO error 212. It is not yet 5 months since the original token acquisitions, and thus
    #         a refresh cannot be performed.
    #
    #     TokensExpired
    #         QBO error 270. The 30 day window has already passed when a token refresh can be performed.
    #
    #     InvalidReconnectRequest
    #         QBO errors 22 or 24 are returned in the XML.
    #
    #     UnknownError
    #         If an unrecognised QBO error code was provided back in the XML.
    #
    #     XMLError
    #         If OAuthToken and OAuthTokenSecret are not found in the XML.
    #     """
    #     assert company in self.companies
    #
    #     qbo_xml_namespace = self.QBO_XML_NAMESPACE
    #
    #     xml = ET.fromstring(response_xml)
    #     error_code = xml.find('{}ErrorCode'.format(qbo_xml_namespace)).text
    #     # It's prior to the 30 day refresh window, so ignore the response.
    #     if error_code == '212':
    #         delta = arrow.now() - arrow.get(self.config[company.upper()]['access_date'])
    #         raise RefreshOutOfWindow(
    #             'Refresh attempted outside of the 5 to 6 month window. It has been {} days since the tokens for {} were acquired.'.format(
    #                 delta.days, company))
    #     # The OAuth access tokens have expired which means that they were not properly updated
    #     # within the 30 day window. Alert the user.
    #     elif error_code == '270':
    #         raise TokensExpired(
    #             "Reconnect endpoint returned error: 270 - The OAuth access token has expired."
    #         )
    #     # There's some other error with the request.
    #     elif error_code in ('22', '24'):
    #         raise InvalidReconnectRequest(
    #             "The reconnect request is not properly formed or includes incorrect tokens."
    #         )
    #     # The reconnect request succeeded so we need to store the new OAuth tokens.
    #     elif error_code == '0':
    #         access_key = xml.find('{}OAuthToken').text
    #         access_secret = xml.find('{}OAuthTokenSecret'.format(qbo_xml_namespace)).text
    #         if access_key and access_secret:
    #             self.update_config_access_keys(company, access_key, access_secret)
    #             return True
    #         else:
    #             raise XMLError("The XML returned from the reconnect endpoint could not be parsed.")
    #     else:
    #         error_message = xml.find('ErrorMessage')
    #         raise UnknownError(
    #             "The following unknown error was returned by the reconnect endpoint: {}".format(error_message)
    #         )

    def update_config_access_keys(self, company, access_key, access_secret):
        """Write the `access_key` and `access_secret` to the provided `config` for `company`, and
        write the result to `opened_secrets_file`. The access_date field will be set to the current
        date.

        Parameters
        ----------
        company : str
            The company to save `access_key` and `access_secret` to.

        access_key : str
            The new access key

        access_secret : str
            The new access secret.

        Returns
        -------
        return : None
            Writes `QBO_API.config` to `QBO_API.secrets_file` with the new access tokens.
        """
        c = company.upper()
        self.config[c]['access_key'] = access_key
        self.config[c]['access_secret'] = access_secret
        self.config[c]['access_date'] = date.today().isoformat()
        self.save_config()


def load_wolfepak_deposits_export(data):
    """Helper for converting a tab delimited and newline separated list of
    WolfePak deposits to a list of dictionaries.

    Parameters
    ----------
    data : str
        A tab and newline delimited block of text to be parsed into input appropriate for
        the `create_purchaser_clearing_deposits` routine.

    Returns
    -------
    return : List[dict]
        [ { purchaser_code: str   # The two character CDEX code
          , purchaser_name: str   # The purchaser's DisplayName
          , reference: str        # A unique reference to the deposit: (batch #)-(line #)
          , amount: str           # The dollar amount of the deposit.
          }
        , ...
        ]
    """
    rows = []
    for line in data.split('\n'):
        rows.append(line.split('\t'))

    return [
        {'purchaser_code': x[0]
            , 'purchaser_name': x[1]
            , 'reference': x[2]
            , 'amount': x[3]
         }
        for x in rows
    ]


def parse_journal_entries(json_response, account_id=None):
    """A generator that yields a flat record from the hierarchical data structure returned by
    QuickBooks from their JournalEntry table.

    Parameters
    ----------
    json_response : dict
        The dict form of the JSON response returned by the JournalEntry resource.

    Yields
    ------
    yield : dict
        { line_id
        , account_id
        , account_name
        , description
        , line_type
        , line_amount
        , txn_date
        }
    """
    header = ['line_id', 'account_id', 'account_name', 'description', 'line_type', 'line_amount', 'txn_date']
    if 'JournalEntry' in json_response['QueryResponse']:
        for entry in json_response['QueryResponse']['JournalEntry']:
            for line in entry['Line']:
                # Filter by `account_id` if it was provided.
                account_id_ = line['JournalEntryLineDetail']['AccountRef']['value']
                if account_id and account_id != account_id_:
                    continue

                txn_date = entry['TxnDate']
                line_id = line['Id']
                account_name = line['JournalEntryLineDetail']['AccountRef']['name']
                description = line.get('Description', None)
                line_type = line['JournalEntryLineDetail']['PostingType']
                line_amount = line['Amount']
                row = (line_id, account_id, account_name, description, line_type, line_amount, txn_date)
                row_dict = dict(zip(header, row))
                yield row_dict
    else:
        yield {col: '' for col in header}


def parse_customers(json_response):
    """`json_response` as returned by `request_query_resource`, which does not include the
    QueryResponse key or the resource name key.
    """
    header = ['id', 'company_name', 'display_name']
    for entry in json_response:
        customer_id = entry['Id']
        display_name = entry['DisplayName']
        # If the CompanyName does not exist, then QBO does not
        # provide the key at all instead of mapping it to None
        # or empty string, so use `get`.
        company_name = entry.get('CompanyName', None)
        row = (customer_id, company_name, display_name)
        row_dict = dict(zip(header, row))
        yield row_dict


def parse_purchaser_clearing_deposits(json_response, purchaser_clearing_account_id):
    header = ['deposit_id', 'line_id', 'purchaser',
              'check_number', 'line_amount', 'total_amount', 'txn_date']
    if 'Deposit' in json_response['QueryResponse']:
        for entry in json_response['QueryResponse']['Deposit']:
            deposit_id = entry['Id']
            total_amount = entry['TotalAmt']
            txn_date = entry['TxnDate']
            for line in entry['Line']:
                # We only want purchaser clearing deposits, so continue if we find
                # a different AccountRef.
                account_id = line['DepositLineDetail']['AccountRef']['value']
                if account_id != purchaser_clearing_account_id:
                    continue

                line_id = line['Id']
                entity = line['DepositLineDetail'].get('Entity', None)
                purchaser = entity['name'] if entity else None
                # The `CheckNum` field is not available through a standard UI report in QBO. When
                # it's not populated, the key does not exist.
                check_number = line['DepositLineDetail'].get('CheckNum', None)
                line_amount = line['Amount']
                row = (deposit_id, line_id, purchaser, check_number, line_amount, total_amount, txn_date)
                row_dict = dict(zip(header, row))
                yield row_dict


def parse_purchaser_clearing_checks(json_response, purchaser_clearing_id):
    header = [
        'purchase_id', 'line_id', 'txn_date',
        'purchaser', 'line_amount', 'total_amount']
    if 'Purchase' in json_response['QueryResponse']:
        for entry in json_response['QueryResponse']['Purchase']:
            purchase_id = entry['Id']
            if 'EntityRef' not in entry:
                continue
            purchaser = entry['EntityRef']['name']
            txn_date = entry['TxnDate']
            total_amount = entry['TotalAmt']
            for line in entry['Line']:
                line_id = line['Id']
                line_amount = line['Amount'] * -1
                account_id = line['AccountBasedExpenseLineDetail']['AccountRef']['value']
                if account_id == purchaser_clearing_id:
                    yield dict(zip(
                        header,
                        (purchase_id, line_id, txn_date, purchaser, line_amount, total_amount)))


def parse_general_ledger(json_response):
    header = ['account_name', 'account_total']
    rows = json_response['Rows']
    if 'Row' in rows:
        for row in rows['Row']:
            account_name = row['Summary']['ColData'][0]['value']
            account_total = row['Summary']['ColData'][6]['value']
            yield dict(
                zip(header, [account_name, account_total])
            )


def request_resource(realm_id, oauth, resource_url, floats_as_decimals=False):
    """Combine `qbo_base_url`, `realm_id`, and `resource_url` into the
    complete URL to make a successful request. The `oauth` object will be
    provided to `requests.get` as its `auth` keyword.

    Parameters
    ----------
    qbo_base_url : str
        The base URL for the QuickBooks API.

    realm_id : str or int
        The company ID specific to each QuickBooks company.

    oauth : oauthlib.OAuth1
        The `OAuth1` object for authorization of the request.

    resource_url : str
        The trailing portion of the URL that includes the resource name
        and its query parameters, that should follow the trailing slash.

        ex: request_resource('account/65')

    Returns
    -------
    return : dict
        A dict that is the JSON response of the resource.

    Raises
    ------
    RequestFailed
        If the expected 'QueryResponse' is not in the returned JSON or a non-200 status code was returned.
    """

    url = 'https://quickbooks.api.intuit.com/v3/company/{}/{}'.format(realm_id, resource_url)

    header = {'Authorization': oauth, 'Accept': 'application/json', 'Content-Type': 'application/text'}
    response = requests.get(
        url=url,
        headers=header)

    if response.status_code != 200:
        raise Exception("{} : {}\n\n{}".format(response.status_code, response.reason, response.text))

    if floats_as_decimals:
        response_json = response.json(parse_float=dec.Decimal)
    else:
        response_json = response.json()

    return response_json


def request_query_resource(realm_id, oauth, resource, query, max_results=None, debug=False):
    """Pass a the pseudo SQL query to the query parameter of the QBO resource endpoint.

    ex:

        Customer?query=SELECT * FROM Customer WHERE id = 1

    Parameters
    ----------
    qbo_base_url : str
        The base URL for the QuickBooks API.

    realm_id : str or int
        The company ID specific to each QuickBooks company.

    oauth : oauthlib.OAuth1
        The `OAuth1` object for authorization of the request.

    resource : str
        A title-cased QBO resource name.

    query : str
        The pseudo SQL query to pass to the QBO endpoint.

    max_results : int
        The maximum number of results to return from the request.

    Returns
    -------
    return : List[dict]
        A list of the JSON results returned by the endpoint.

    Raises
    ------
    RC_QBO_Exception
        If `max_results` is greater than the maximum MAXRESULTS that QBO will accept.
    """
    if max_results:
        if max_results > batch_dict['max_results']:
            raise Exception("""QuickBooks will only return a maximum of {} configured with
                            the 'max_results' batch_dict key.""".format(batch_dict['max_results']))
    else:
        max_results = batch_dict['max_results']

    next_start = 1
    resource_url = "query?query={} STARTPOSITION {} MAXRESULTS {}".format(query, next_start, max_results)
    json_response = request_resource(realm_id, oauth, resource_url)

    all_records = json_response['QueryResponse'][resource]
    while json_response['QueryResponse']['maxResults'] == max_results:
        next_start = next_start + max_results
        resource_url = "query?query={} STARTPOSITION {} MAXRESULTS {}".format(query, next_start, max_results)
        json_response = request_resource(realm_id, oauth, resource_url, debug=debug)

        records = json_response['QueryResponse'][resource]
        if len(records) > 0:
            all_records.extend(records)

    return all_records


def create_resource(realm_id, oauth, resource_url, resource, dry_run=False, **kwargs):
    """Combine `qbo_base_url`, `realm_id`, and `resource_url` into the
    complete URL to make a successful post request to create a resource. The `oauth` object
    will be provided to `requests.post` as its `auth` keyword.

    Parameters
    ----------
    qbo_base_url : str
        The base URL for the QuickBooks API.

    realm_id : str or int
        The company ID specific to each QuickBooks company.

    oauth : oauthlib.OAuth1
        The `OAuth1` object for authorization of the request.

    resource_url : str
        The title-cased QBO resource name, such as: Customer.

    resource : dict
        A dict that will be converted to the JSON representation of the resource to be
        created and passed to the `json` parameter of `requests.post`.

    dry_run : bool = False
        Print the POST parameters instead of sending the actual request.

    **kwargs : json.loads(**kwargs)
        Pass additional kwargs to `requests.Response.json` which is utimately
        passed to `json.loads`.

    Returns
    -------
    return : dict
        A dict that is the JSON response of the created resource,
        or the POST parameters if `dry_run` is True.

    Raises
    ------
    PostFailed
        If a status code other than 200 was returned.
    """

    url = 'https://quickbooks.api.intuit.com/v3/company/{}/{}?minorversion=12'.format(realm_id, resource_url)
    headers = {"Authorization": oauth, "Accept": "application/json", "Content-Type": "application/json",
               'User-Agent': 'RC_QBO_Reporting'}

    if dry_run:
        print("URL:")
        print("HEADERS")
        print("-------")
        pprint(headers)
        print("RESOURCE")
        print("--------")
        pprint(resource)
        return {
            'url': url,
            'headers': headers,
            'resource': resource
        }
    else:

        response = requests.post(
            url=url,
            headers=headers,
            data=json_dumps(resource)
        )
        if response.status_code != 200:
            raise PostFailed(f"{response.status_code} : {response.reason}\n\n{response.text}")

        return response.json(**kwargs)


def purchaser_to_customer(p):
    note_data = {
        'cluster_id': p['ClusterID'],
        'entity': p['PurchaserEntity'],
        'owner_num': p['PurchaserOwnerNumber']
    }
    customer = {
        "BillAddr": {
            "Line1": p['cass_street1'],
            "Line2": p['cass_street2'],
            "City": p['cass_city'],
            "CountrySubDivisionCode": p['cass_state'],
            "PostalCode": p['cass_zip']
        },
        "CompanyName": p['PurchaserCode'],
        "DisplayName": p['PurchaserName'],
        "Notes": encode_note_data(note_data)
    }
    return customer


def encode_note_data(data):
    """Create a string from a dictionary to store in a QBO notes field.

    Parameters
    ----------
    data : dict
        Key value pairs to store in a QBO notes field.

    Returns
    -------
    return : str
        A string of the format below:
            key1: value1\n
            key2: value2\n

        ':' or '\n' in the key or value will raise a ValueError exception.

    Raises
    ------
    ValueError
        If ':' or '\n' were in a key or value.
    """
    text = ""
    for key, val in data.items():
        if ':' in val or '\n' in val:
            raise ValueError("The note data value cannot contain a colon or newline.")
        if ':' in key or '\n' in key:
            raise ValueError("The note data key cannot contain a colon or newline.")
        text += "{}: {}\n".format(key, val)

    return text


def create_resources(qbo_base_url, realm_id, oauth, resource_name, resources):
    """Use the QBO batch API to create multiple resources at once. Up to 30 operations can
    be sent in each batch. Additional details for the batch API can be found here:

        https://developer.intuit.com/docs/api/accounting/batch

    !! WARNING !!

    This routine does not check for business errors raised by QBO. The return value
    should be checked for a 'Fault' key to see if each resource creation actually
    succeeded.

    !! END WARNING !!

    Parameters
    ----------

    qbo_base_url : str
        The base URL for the QuickBooks API.

    realm_id : str or int
        The company ID specific to each QuickBooks company.

    oauth : oauthlib.OAuth1
        The `OAuth1` object for authorization of the request.

    resource_name : str
        The title-cased version of the resource name, as specified
        in QBO, such as: Vendor

    resources : List[dict]
        A list of dict objects that will be converted to the JSON representation of the
        resources to be created.

    Returns
    -------
    return : (exception, batch_response, resources)
        exception : Exception raised during an intermediate batch update chunk
        batch_response : A dict that is the JSON response for BatchItemRequest API, so far
                         if an exception as raised.
        resources : The `resources` parameter that was passed in for error handling.
    """
    url = "{}/company/{}/batch".format(qbo_base_url, realm_id)
    headers = {
        'Accept': 'application/json',
        'content-type': 'application/text; charset=utf-8',
        'User-Agent': 'RC_QBO_Reporting'
    }

    batch_item_response = []

    TOKENS_FILE = r'{}\utils\tokens.cfg'.format(BASE_DIR)
    token_config = ConfigParser()
    token_config.read(TOKENS_FILE)

    exception = None
    resource_idx = 0
    chunk_start = 0
    chunk_end = chunk_start + batch_dict['batch_item_limit']
    num_resources = len(resources)
    while chunk_start <= num_resources:
        try:
            batch_item_request = []
            for resource in resources[chunk_start:chunk_end]:
                batch_item = {"bId": "{}".format(resource_idx), "operation": "create", resource_name: resource}
                batch_item_request.append(batch_item)

                resource_idx += 1

            payload = {"BatchItemRequest": batch_item_request}

            chunk_start += batch_dict['batch_item_limit']
            chunk_end = chunk_start + batch_dict['batch_item_limit']

            response = requests.post(
                url=url,
                auth=oauth,
                headers=headers,
                data=json_dumps(payload)
            )

            response_json = response.json()['BatchItemResponse']
        except Exception as e:
            exception = e
            break

        batch_item_response.extend(response_json)

    return exception, batch_item_response, resources


def update_resources(qbo_base_url, realm_id, oauth, resource_name, resources):
    """Use the QBO batch API to update multiple resources at once. Up to 30 operations can
    be sent in each batch. Additional details for the batch API can be found here:

        https://developer.intuit.com/docs/api/accounting/batch

    Parameters
    ----------
    qbo_base_url : str
        The base URL for the QuickBooks API.

    realm_id : str or int
        The company ID specific to each QuickBooks company.

    oauth : oauthlib.OAuth1
        The `OAuth1` object for authorization of the request.

    resource_name : str
        The title-cased version of the resource name, such as: Vendor

    resources : List[dict]
        A list of dict objects that will be converted to the JSON representation of the
        resources to be updated. Each resource in `resources` must contain the `Id` field
        for the resource to be updated.

    Returns
    -------
    return : (exception, batch_response, resources)
        exception : Exception raised during an intermediate batch update chunk
        batch_response : A dict that is the JSON response for BatchItemRequest API, so far
                         if an exception as raised.
        resources : The `resources` parameter that was passed in for error handling.

    Raises
    ------
    PostFailed
        If a non-200 status code was returned.
    """
    url = "{}/company/{}/batch".format(qbo_base_url, realm_id)
    headers = {
        'Accept': 'application/json',
        'content-type': 'application/json; charset=utf-8',
        'User-Agent': 'RC_QBO_Reporting'
    }

    batch_item_response = []

    TOKENS_FILE = r'{}\utils\tokens.cfg'.format(BASE_DIR)
    token_config = ConfigParser()
    token_config.read(TOKENS_FILE)

    exception = None
    resource_idx = 0
    chunk_start = 0
    chunk_end = chunk_start + batch_dict['batch_item_limit']
    num_resources = len(resources)
    while chunk_start <= num_resources:
        try:
            batch_item_request = []
            for resource in resources[chunk_start:chunk_end]:
                batch_item = {"bId": "{}".format(resource_idx), "operation": "update", resource_name: resource}
                batch_item_request.append(batch_item)

                resource_idx += 1

            payload = {"BatchItemRequest": batch_item_request}

            chunk_start += batch_dict['batch_item_limit']
            chunk_end = chunk_start + batch_dict['batch_item_limit']

            response = requests.post(
                url=url,
                auth=oauth,
                headers=headers,
                data=json_dumps(payload))

            response_json = response.json()['BatchItemResponse']
        except Exception as e:
            exception = e
            break

        batch_item_response.extend(response_json)

    return exception, batch_item_response, resources


def write_batch_results(batch_response, resources):
    """Write the input and output of the batch methods to a file."""
    filename = '{}.txt'.format(unique_filename(prefix='load_purchasers_response'))
    print("[INFO] Dumping intermediate results to {}..".format(filename))
    try:
        output = {
            'batch_response': batch_response,
            'resources': resources
        }
        with open(filename, 'w') as out:
            out.write(json_dumps(output))
    except Exception as e:
        print("[ERROR] Failed to write batch response file: {}\n\n{}".format(filename, str(e)))


def handle_batch_failure(exception, batch_response, resources):
    """Handles failures from QBO batch routines `update_resources` and `create_resources`.

    Write the batch results and resources to a file and start PDB if the batch contained
    Fault records or if an exception was raised by the `create_resources` routine, otherwise
    just return the `batch_response`.
    """
    if exception:
        print("[ERROR] An exception was raised during the QBO batch process.")
        write_batch_results(batch_response, resources)
        print("[INFO] Processed {} of {} resources.".format(len(batch_response), len(resources)))
        print("[INFO] Starting PDB..")
        import pdb
        pdb.set_trace()
    else:
        faults = list(filter(lambda x: 'Fault' in x, batch_response))
        if faults:
            write_batch_results(batch_response, resources)
            fault_ids = [int(f['bId']) for f in faults]
            fault_records = list(map(resources.__getitem__, fault_ids))
            print("[INFO] QBO batch had faults. Starting PDB..")
            print("[INFO] .. variable `fault_records` contains the issue records.")
            import pdb
            pdb.set_trace()
        else:
            return batch_response


def chart_of_accounts_to_matrix(companies, chart_of_accounts):
    """Create an account by company 2D matrix identifying which
    accounts exists for which companies.

    ex:

              CYPT  FOOT
        1010   X     _
        4150   X     X

    Parameters
    ----------

    companies : List[str]
        The list of companies to generate the matrix for.

    chart_of_accounts : List[Tuple]
        The chart of accounts as generated by `retrieve_chart_of_accounts`.

    Returns
    -------
    return : List[List]
        See example above.
    """
    accounts = defaultdict(list)
    for company, account_id, account_name, account_type, account_sub_type in chart_of_accounts:
        key = (account_id, account_name, account_type, account_sub_type)
        accounts[key].append(company)

    account_map = defaultdict(dict)
    for account in accounts.keys():
        for company in companies:
            if company in accounts[account]:
                account_map[account][company] = 'X'
            else:
                account_map[account][company] = ''

    coa_matrix = []
    for key, val in account_map.items():
        account_id, account_name, account_type, account_sub_type = key
        row = [' '.join([account_id, account_name]).strip(), account_type, account_sub_type]
        for company in companies:
            row.append(val[company])
        coa_matrix.append(row)

    return coa_matrix

"""gspread Wrapper."""

import logging
import random

import gspread
import vcr
from icecream import ic
from tenacity import retry, stop_after_attempt
from tenacity.retry import retry_if_not_exception_type
from tenacity.wait import wait_exponential

ic.configureOutput(includeContext=True)

# ic.disable()

DEFAULT_CREDENTIAL_TYPE = "service_account"
DEFAULT_CREDENTIAL_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class DtkGspread:
    """gspread Wrapper."""

    def __init__(
        self,
        credentials: str | list[str] | list[dict],
        credentials_type: str = DEFAULT_CREDENTIAL_TYPE,
        credential_scopes: list[str] = DEFAULT_CREDENTIAL_SCOPES,
        oauth_credentials_filename: str = None,
        oauth_authorized_user_filename: str = None,
    ) -> None:
        """Initialize the gspread wrapper.

        Args:
            credentials (str | list[str] | list[dict]): The credentials to use for logging in.
            credentials_type (str): The type of credentials to use. Can be "oauth" or "service_account".
            credential_scopes (list[str]): The scopes to use for the credentials.
            oauth_credentials_filename (str): The path to the OAuth credentials file.
            oauth_authorized_user_filename (str): The path to the authorized user file.
        """
        # We store logged-in clients in a list so that we can use
        # multiple accounts which helps with rate limiting trumendously
        self.logged_in_clients: list[gspread.Client] = []

        # Set the selected client to None
        self.__selected_client: int | None = None

        logging.debug("Selected credential type: %s", ic(credentials_type))
        if credentials_type == "oauth":
            # Login with the OAuth credentials
            oauth_gc, oauth_authorized_user = gspread.oauth(
                scopes=credential_scopes,
                credentials_filename=oauth_credentials_filename,
                authorized_user_filename=oauth_authorized_user_filename,
            )
            self.logged_in_clients.append(oauth_gc)
        else:
            # Login with the service accounts
            self._retrieve_service_accounts(credentials, credential_scopes)

        # Set the clients cache
        self.__clients_cache: list[gspread.Client] = self.logged_in_clients.copy()

    def _retrieve_service_accounts(
        self, credentials: str | list[str], credential_scopes: list[str]
    ) -> None:
        ic(credentials)
        if not isinstance(credentials, list):
            credentials = [credentials]
        logging.debug("Number of credentials provided: %s", ic(len(credentials)))

        # Go through each credential, login with each one and add it
        # to the list of logged in clients
        for credential in credentials:
            # If the credential is a string, it's a path to a json file
            if isinstance(credential, str) and credential.endswith(".json"):
                self.logged_in_clients.append(
                    gspread.service_account(filename=credential, scopes=credential_scopes)
                )
                continue

            # If the credential is a dictionary, it's a dictionary
            # of credentials
            if isinstance(credential, dict):
                self.logged_in_clients.append(
                    gspread.service_account_from_dict(credential, scopes=credential_scopes)
                )
                continue

            raise ValueError("Invalid credential!")

    @property
    def client(self) -> gspread.Client:
        """Retrieve a random client from the list of logged in clients. This will allow you to do custom operations on the client."""
        # Check if cache is empty
        if ic(len(self.__clients_cache)) == 0:
            logging.debug(ic("Cache is empty, repopulating with logged in clients"))
            self.__clients_cache = self.logged_in_clients.copy()

        # Get a random index
        self.__selected_client = random.randint(0, len(self.__clients_cache) - 1)

        # Get the selected client
        selected_client: gspread.Client = self.__clients_cache[self.__selected_client]

        # Remove the selected client from the __clients_cache
        self.__clients_cache.pop(self.__selected_client)

        return selected_client

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
        # Only if it's valid gspread errors
        # TODO: Possible improvement: Add a custom method that checks the error code and retries based on that so we don't retry on every error
        retry=(
            retry_if_not_exception_type(ValueError)
            & retry_if_not_exception_type(gspread.SpreadsheetNotFound)
            & retry_if_not_exception_type(gspread.NoValidUrlKeyFound)
        ),
    )
    def __get_spreadsheet(
        self, spreadsheet_id: str = None, spreadsheet_name: str = None, spreadsheet_url: str = None
    ) -> gspread.Spreadsheet:
        """Get a spreadsheet by ID, name, or URL.

        Args:
            spreadsheet_id (str): The ID of the spreadsheet.
            spreadsheet_name (str): The name of the spreadsheet.
            spreadsheet_url (str): The URL of the spreadsheet.

        Returns:
            The spreadsheet object.
        """
        # If spreadsheet_id is provided, use it
        if spreadsheet_id:
            logging.debug("Spreadsheet ID provided: %s", ic(spreadsheet_id))
            return self.client.open_by_key(spreadsheet_id)

        # If spreadsheet_name is provided, use it
        if spreadsheet_name:
            logging.debug("Spreadsheet name provided: %s", ic(spreadsheet_name))
            return self.client.open_by_url(spreadsheet_name)

        # If spreadsheet_url is provided, use it
        if spreadsheet_url:
            logging.debug("Spreadsheet URL provided: %s", ic(spreadsheet_url))
            return self.client.open_by_url(spreadsheet_url)

        # If none of the above are provided, raise an error
        raise ValueError("No spreadsheet ID, name, or URL provided.")

    def get_spreadsheet(
        self, spreadsheet_id: str = None, spreadsheet_name: str = None, spreadsheet_url: str = None
    ) -> gspread.Spreadsheet:
        """Get a spreadsheet by ID, name, or URL (provide one).

        Args:
            spreadsheet_id (str): The ID of the spreadsheet.
            spreadsheet_name (str): The name of the spreadsheet.
            spreadsheet_url (str): The URL of the spreadsheet.

        Returns:
            The spreadsheet object.
        """
        return self.__get_spreadsheet(spreadsheet_id, spreadsheet_name, spreadsheet_url)


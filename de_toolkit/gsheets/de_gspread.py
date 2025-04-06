"""Google Sheets Wrapper."""

import logging

import gspread
import vcr
from icecream import ic

ic.configureOutput(includeContext=True)


class DtkGspread:
    """gspread wrapper."""

    def __init__(
        self,
        credentials: str | list[str] | list[dict],
        credentials_type: str = None,
        credential_scopes: list[str] = None,
        oauth_credentials_filename: str = None,
        oauth_authorized_user_filename: str = None,
    ) -> None:
        """Initialize the gspread wrapper.

        Args:
            credentials: The credentials to use for logging in.
            credentials_type: The type of credentials to use. Can be "oauth" or "service_account".
            credential_scopes: The scopes to use for the credentials.
            oauth_credentials_filename: The path to the OAuth credentials file.
            oauth_authorized_user_filename: The path to the authorized user file.
        """
        # We store logged-in clients in a list so that we can use
        # multiple accounts which helps with rate limiting trumendously
        self.logged_in_clients = []

        logging.debug(ic(credentials_type))
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

    def _retrieve_service_accounts(
        self, credentials: str | list[str], credential_scopes: list[str]
    ) -> None:
        ic(credentials)
        if not isinstance(credentials, list):
            credentials = [credentials]
        logging.debug(ic(len(credentials)))

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

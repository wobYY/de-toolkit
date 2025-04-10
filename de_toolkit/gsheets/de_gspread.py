"""gspread Wrapper."""

import logging
import random
import string

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

    def __verify_spreadsheet_was_provided(
        self, provided_spreadsheet: gspread.Spreadsheet | str, assume_spreadsheet_id: bool = True
    ) -> gspread.Spreadsheet:
        """Verify spreadsheet was provided and return the spreadsheet object if it wasn't.

        Args:
            provided_spreadsheet (gspread.Spreadsheet | str): The spreadsheet object or, spreadsheet ID or spreadsheet name.
            assume_spreadsheet_id (bool): Whether to assume the provided "spreadsheet", when it's a string, is a spreadsheet ID or spreadsheet name. Defaults to True.

        Returns:
            The spreadsheet object.
        """
        if isinstance(provided_spreadsheet, gspread.Spreadsheet):
            return provided_spreadsheet

        # If assume_spreadsheet_id is True, assume the provided "spreadsheet"
        # is a spreadsheet ID
        if assume_spreadsheet_id:
            return self.get_spreadsheet(spreadsheet_id=provided_spreadsheet)

        # Otherwise assume the provided "spreadsheet" is a spreadsheet name
        return self.get_spreadsheet(spreadsheet_name=provided_spreadsheet)

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
        # Only if it's valid gspread errors
        # TODO: Possible improvement: Add a custom method that checks the error code and retries based on that so we don't retry on every error
        retry=(
            retry_if_not_exception_type(ValueError)
            & retry_if_not_exception_type(TypeError)
            & retry_if_not_exception_type(gspread.WorksheetNotFound)
        ),
    )
    def __get_worksheet(
        self,
        spreadsheet: gspread.Spreadsheet,
        worksheet_id: str | int = None,
        worksheet_name: str = None,
        worksheet_index: int = None,
    ) -> gspread.Worksheet:
        """Get a worksheet by ID, name or index.

        Args:
            spreadsheet (gspread.Spreadsheet): The spreadsheet object.
            worksheet_id (str | int): The ID of the worksheet.
            worksheet_name (str): The name of the worksheet.
            worksheet_index (int): The index of the worksheet.

        Returns:
            The worksheet object.
        """
        # If worksheet_id is provided, use it
        if worksheet_id:
            logging.debug("Worksheet ID provided: %s", ic(worksheet_id))
            return spreadsheet.get_worksheet_by_id(int(worksheet_id))

        # If worksheet_name is provided, use it
        if worksheet_name:
            logging.debug("Worksheet name provided: %s", ic(worksheet_name))
            return spreadsheet.worksheet(worksheet_name)

        # If worksheet_index is provided, use it
        if worksheet_index:
            logging.debug("Worksheet index provided: %s", ic(worksheet_index))
            return spreadsheet.get_worksheet(worksheet_index)

        # If none of the above are provided, raise an error
        raise ValueError("No worksheet ID or name provided.")

    def get_worksheet(
        self,
        spreadsheet: gspread.Spreadsheet | str,
        worksheet_id: str | int = None,
        worksheet_name: str = None,
        worksheet_index: int = None,
        **kwargs,
    ) -> gspread.Worksheet:
        """Get a worksheet by ID or name (provide one).

        Args:
            spreadsheet (gspread.Spreadsheet | str): The gspread spreadsheet object or, spreadsheet ID or spreadsheet name.
            worksheet_id (str | int): The ID of the worksheet.
            worksheet_name (str): The name of the worksheet.
            worksheet_index (int): The index of the worksheet.

        Keyword Args:
            assume_spreadsheet_id (bool): Whether to assume the provided "spreadsheet", when it's a string, is a spreadsheet ID or spreadsheet name. Defaults to True.

        Returns:
            The worksheet object.
        """
        # Verify spreadsheet was provided
        spreadsheet = self.__verify_spreadsheet_was_provided(spreadsheet, **kwargs)

        # Get and return the worksheet
        return self.__get_worksheet(spreadsheet, worksheet_id, worksheet_name, worksheet_index)

    def get_list_of_worksheets(
        self, spreadsheet: gspread.Spreadsheet, exclude_hidden_worksheets: bool = False, **kwargs
    ) -> list[gspread.Worksheet]:
        """Get a list of worksheets from a spreadsheet.

        Args:
            spreadsheet (gspread.Spreadsheet): The spreadsheet object.
            exclude_hidden_worksheets (bool): Whether to exclude hidden worksheets.

        Keyword Args:
            assume_spreadsheet_id (bool): Whether to assume the provided "spreadsheet", when it's a string, is a spreadsheet ID or spreadsheet name. Defaults to True.

        Returns:
            A list of worksheet objects.
        """
        # Verify spreadsheet was provided
        spreadsheet = self.__verify_spreadsheet_was_provided(spreadsheet, **kwargs)

        # Get the list of worksheets
        return spreadsheet.worksheets(exclude_hidden=exclude_hidden_worksheets)

    def __random_string_generator(
        self, length: int = 5, prefix: str = None, suffix: str = None
    ) -> str:
        """Generate a random string of the specified length."""
        characters = string.ascii_letters + string.digits

        return (
            (prefix + "_" if prefix else "")
            + "".join(random.choice(characters) for i in range(length))
            + ("_" + suffix if suffix else "")
        )

    def __unique_column_name_from_list(
        self,
        list_of_columns: list[str],
        list_for_unique_cols: list[str] | None,
        string_as_suffix: bool,
    ) -> list[str]:
        # TODO: Add docstirngs
        processed_columns = []
        for column in list_of_columns:
            if list_for_unique_cols is not None and len(list_of_columns.count(column)) > len(
                list_for_unique_cols
            ):
                raise ValueError(
                    f"There are {len(list_of_columns.count(column))} columns with the same name but only {len(list_for_unique_suffixes)} unique suffixes provided."
                )

            if list_of_columns.count(column) == 1:
                processed_columns.append(column)
                continue

            if list_for_unique_cols is not None:
                for unique_str in list_for_unique_cols:
                    if string_as_suffix and f"{column}_{unique_str}" not in processed_columns:
                        processed_columns.append(ic(f"{column}_{unique_str}"))
                        break

                    if not string_as_suffix and f"{unique_str}_{column}" not in processed_columns:
                        processed_columns.append(ic(f"{unique_str}_{column}"))
                        break

                    continue

            if string_as_suffix:
                generated_str = self.__random_string_generator(
                    prefix=column if string_as_suffix else None,
                    suffix=None if string_as_suffix else column,
                )

                # In the rare case that the generated string is already in the
                # list of processed columns, generate a new string and repeat
                # the process until a unique string is generated
                while generated_str in processed_columns:
                    generated_str = self.__random_string_generator(
                        prefix=column if string_as_suffix else None,
                        suffix=None if string_as_suffix else column,
                    )

                processed_columns.append(ic(generated_str))
                continue

        # Return the processed columns
        return processed_columns

    def __get_worksheet_values(
        self,
        worksheet: gspread.Worksheet,
        sheet_range: str = None,
        major_dimension: str = "rows",
        value_render_option: str = "formatted",
        header: int | None = 1,
        header_column_names: list[str] | None = None,
        replace_empty_strings_with_none: bool = False,
        suffixes_for_uniquifying_columns: list[str] | None = None,
        random_string_as_suffix: bool = True,
        **kwargs,
    ) -> list[list]:
        # TODO: Add docstrings
        # If header is None the header_column_names must be provided
        if header is None and header_column_names is None:
            raise ValueError("Either header or header_column_names must be provided.")

        # Major Dimension - Can be either "rows" or "columns"
        major_dimension = gspread.utils.Dimension[major_dimension.lower()]

        # Value Render Option - Can be either "formatted", "unformatted" or "formula"
        value_render_option = gspread.utils.ValueRenderOption[value_render_option.lower()]

        # Get the values from the worksheet
        worksheet_data = worksheet.get(
            range_name=sheet_range,
            major_dimension=major_dimension,
            value_render_option=value_render_option,
            **kwargs,
        )

        # If replace_empty_strings_with_none is True, replace empty strings with None.
        # For each list in the list of lists, replace empty strings with None
        if replace_empty_strings_with_none:
            logging.debug("Replacing empty strings with None")
            for row in worksheet_data:
                row = [None if cell_value == "" else cell_value for cell_value in row]

        # Get header_columns as either worksheet_data[header] or header_column_names
        header_columns = worksheet_data[header - 1] if header is not None else header_column_names
        logging.debug("Header columns: %s", ic(header_columns))

        # Ensure that the selected header has unique values
        if len(set(header_columns)) != len(header_columns):
            logging.info(
                "Header column names are not unique, %s.",
                "generating random column names"
                if suffixes_for_uniquifying_columns is None
                else "using provided list",
            )
            header_columns = self.__unique_column_name_from_list(
                header_columns,
                suffixes_for_uniquifying_columns,
                random_string_as_suffix,
            )
            logging.debug("Uniqified header columns: %s", ic(header_columns))

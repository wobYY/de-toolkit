"""Unit tests for de_gspread."""

import pytest

from de_toolkit.gsheets.de_gspread import DtkGspread
from dotenv import load_dotenv
import os
import gspread

# Load environment variables
load_dotenv()

# Create a gspread client
gc = DtkGspread(
    credentials=os.environ["DTK_GSPREAD_CREDENTAILS"],
    credentials_type="service_account",
    credential_scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ],
)


def test_service_acc_invalid_credentials() -> None:
    """Test that the DtkGspread class raises an error when given invalid credentials."""
    with pytest.raises(ValueError, match="Invalid credential!"):
        DtkGspread(credentials="")


def test_oauth_no_credentials() -> None:
    """Test that the DtkGspread class raises an error when given no credentials for OAuth."""
    with pytest.raises(TypeError):
        DtkGspread(credentials="", credentials_type="oauth")


def test_empty_spreadsheet_id() -> None:
    """Test that the DtkGspread class raises an error when given an empty spreadsheet ID."""
    with pytest.raises(ValueError, match="No spreadsheet ID, name, or URL provided."):
        gc.get_spreadsheet(spreadsheet_id="")


def test_empty_spreadsheet_name() -> None:
    """Test that the DtkGspread class raises an error when given an empty spreadsheet name."""
    with pytest.raises(ValueError, match="No spreadsheet ID, name, or URL provided."):
        gc.get_spreadsheet(spreadsheet_name="")


def test_empty_spreadsheet_url() -> None:
    """Test that the DtkGspread class raises an error when given an empty spreadsheet URL."""
    with pytest.raises(ValueError, match="No spreadsheet ID, name, or URL provided."):
        gc.get_spreadsheet(spreadsheet_url="")


def test_invalid_spreadsheet_id() -> None:
    """Test that the DtkGspread class raises an error when given an invalid spreadsheet ID."""
    with pytest.raises(gspread.SpreadsheetNotFound):
        gc.get_spreadsheet(spreadsheet_id="invalid-id")


def test_invalid_spreadsheet_name() -> None:
    """Test that the DtkGspread class raises an error when given an invalid spreadsheet name."""
    with pytest.raises(gspread.NoValidUrlKeyFound):
        gc.get_spreadsheet(spreadsheet_name="invalid-name")


def test_invalid_spreadsheet_url() -> None:
    """Test that the DtkGspread class raises an error when given an invalid spreadsheet URL."""
    with pytest.raises(gspread.NoValidUrlKeyFound):
        gc.get_spreadsheet(spreadsheet_url="invalid-url")


def test_valid_spreadsheet_id() -> None:
    """Test that the DtkGspread class returns a valid spreadsheet object when given a valid spreadsheet ID."""
    spreadsheet = gc.get_spreadsheet(
        spreadsheet_id=os.environ["DTK_GSPREAD_SPREADSHEET_ID"],
    )
    assert isinstance(spreadsheet, gspread.Spreadsheet)

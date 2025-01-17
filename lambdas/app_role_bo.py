"""
This module contains the business logic for the AppRole entity
"""
from functools import lru_cache

from app_common.dynamodb_utils import DynamoDBBase
from app_common.app_utils import http_request


class AppRole:
    """
    Represents a AppRole entity.
    """

    def __init__(
        self,
        app_id: str,
        role_source: str,
    ) -> None:
        self.app_id = app_id
        self.role_source = role_source

    def to_dict(self):
        """
        Generates a dictionary representation of the entity.
        """
        return {
            "app_id": self.app_id,
            "role_source": self.role_source,
        }


class AppRoleBO(DynamoDBBase):
    """Business object for the AppRole entity."""

    def get_role_content(self, app_id: str) -> str:
        """
        Retrieves the role content for the specified application.
        """
        role_source = self.get_role_source(app_id)

        if not role_source:
            return None

        role_content = self._load_url_content_as_text(role_source)

        return role_content

    @lru_cache(maxsize=128)
    def get_role_source(self, app_id: str) -> str:
        """
        Retrieves the prompt for the specified application.
        """
        response = self.get_by_partition_key(pk_name="app_id", pk_value=app_id)

        if not response:  # response is a list
            return None

        # get the first item in the list
        role_source = response[0]["role_source"]

        return role_source

    def _load_url_content_as_text(self, url: str) -> str:
        """
        Loads the content of the specified URL as text.
        """
        response = http_request("GET", url)
        return response.get("body", None)

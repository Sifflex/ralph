"""OVH's LDP storage backend for Ralph"""

import logging
import re
import sys

import ovh
import requests

from ralph.exceptions import BackendParameterException

from ..mixins import HistoryMixin
from .base import BaseStorage

logger = logging.getLogger(__name__)


class LDPStorage(HistoryMixin, BaseStorage):
    """OVH's LDP storage backend"""

    # pylint: disable=too-many-arguments

    name = "ldp"

    def __init__(
        self,
        endpoint,
        application_key,
        application_secret,
        consumer_key,
        service_name=None,
        stream_id=None,
    ):
        self._endpoint = endpoint
        self._application_key = application_key
        self._application_secret = application_secret
        self._consumer_key = consumer_key
        self.service_name = service_name
        self.stream_id = stream_id

        self.client = ovh.Client(
            endpoint=self._endpoint,
            application_key=self._application_key,
            application_secret=self._application_secret,
            consumer_key=self._consumer_key,
        )

    @property
    def _archive_endpoint(self):
        if None in (self.service_name, self.stream_id):
            msg = "LDPStorage backend instance requires to set both service_name and stream_id"
            logger.error(msg)
            raise BackendParameterException(msg)
        return f"/dbaas/logs/{self.service_name}/output/graylog/stream/{self.stream_id}/archive"

    def url(self, name):
        """Get archive absolute URL"""

        download_url_endpoint = f"{self._archive_endpoint}/{name}/url"

        response = self.client.post(download_url_endpoint)
        download_url = response.get("url")
        logger.debug("Temporary URL: %s", download_url)

        return download_url

    def list(self):
        """List archives for a given stream"""

        list_archives_endpoint = self._archive_endpoint
        logger.debug("List archives endpoint: %s", list_archives_endpoint)

        archives = self.client.get(list_archives_endpoint)
        logger.debug("Found %d archives", len(archives))

        return archives

    def read(self, name, chunk_size=4096):
        """Read the `name` archive file and stream its content"""

        logger.debug("Getting archive: %s", name)

        # Stream response (archive content)
        with requests.get(self.url(name), stream=True) as result:
            result.raise_for_status()
            for chunk in result.iter_content(chunk_size=chunk_size):
                sys.stdout.buffer.write(chunk)

        # Archive is supposed to have been fully fetched, add a new entry to
        # the history.
        self.append_to_history(
            {
                "backend": self.name,
                "command": "fetch",
                "id": name,
                "filename": details.get("filename"),
                "size": details.get("size"),
                "fetched_at": datetime.datetime.now(
                    tz=datetime.timezone.utc
                ).isoformat(),
            }
        )

    def write(self, name, content):
        """LDP storage backend is read-only, calling this method will raise an error"""

        msg = "LDP storage backend is read-only, cannot write to %s"
        logger.error(msg, name)
        raise NotImplementedError(msg % name)
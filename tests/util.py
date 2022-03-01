__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import subprocess
from unittest import mock

from octoprint.util import to_bytes


class MockPopen:
    def __init__(self):
        pass

    def communicate(self, input=None):
        pass

    @property
    def returncode(self):
        pass


def setup_mock_popen(expected_stdout, expected_stderr):
    mock_popen = MockPopen()
    mock_popen.communicate = mock.Mock(
        return_value=(
            to_bytes(expected_stdout, encoding="utf-8"),
            to_bytes(expected_stderr, encoding="utf-8"),
        )
    )
    subprocess.Popen = lambda *args, **kwargs: mock_popen

    return mock_popen

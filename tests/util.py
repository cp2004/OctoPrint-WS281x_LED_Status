# -*- coding: utf-8 -*-
import subprocess

import mock
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
    setattr(subprocess, "Popen", lambda *args, **kwargs: mock_popen)

    return mock_popen

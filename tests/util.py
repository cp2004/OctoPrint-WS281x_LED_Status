# -*- coding: utf-8 -*-
import subprocess

import mock


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
            bytes(expected_stdout, encoding="utf-8"),
            bytes(expected_stderr, encoding="utf-8"),
        )
    )
    mock_returncode = mock.PropertyMock(return_value=1)
    type(mock_popen).returncode = mock_returncode
    setattr(subprocess, "Popen", lambda *args, **kwargs: mock_popen)

    return mock_popen

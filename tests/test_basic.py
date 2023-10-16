import json
from pathlib import Path

import main
import pytest
from fastapi.testclient import TestClient


client = TestClient(main.app)


@pytest.fixture(scope="module")
def payload():
    tests_dir = Path(__file__).absolute().parent
    return json.load(open(tests_dir / "test_payload.json"))


def test_post_actions_queued(payload, mocker):
    mocker.patch("main.get_registration_token")
    mocker.patch("main.provision_vm")
    mocker.patch("main.destroy_vm")
    response = client.post("/actions/", json=payload)
    assert response.status_code == 200
    main.get_registration_token.assert_called_once()
    main.provision_vm.assert_called_once()
    main.destroy_vm.assert_not_called()


def test_post_actions_completed(payload, mocker):
    mocker.patch("main.get_registration_token")
    mocker.patch("main.provision_vm")
    mocker.patch("main.destroy_vm")
    payload["action"] = "completed"
    payload["workflow_job"]["runner_name"] = "some-runner"
    response = client.post("/actions/", json=payload)
    assert response.status_code == 200
    main.get_registration_token.assert_not_called()
    main.provision_vm.assert_not_called()
    main.destroy_vm.assert_called_once()

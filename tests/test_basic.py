import json
from pathlib import Path

import job
import main
import pytest
from fastapi.testclient import TestClient


client = TestClient(main.app)


@pytest.fixture(scope="module")
def payload():
    tests_dir = Path(__file__).absolute().parent
    return json.load(open(tests_dir / "test_payload_new.json"))


def test_post_actions_queued(payload, mocker):
    mocker.patch("main.cloud")
    mocker.patch("job.cloud")
    response = client.post("/actions/", json=payload)
    assert response.status_code == 200
    job.cloud.provision_vm.assert_called_once()
    main.cloud.destroy_vm.assert_not_called()


def test_post_actions_completed(payload, mocker):
    mocker.patch("main.cloud")
    mocker.patch("job.cloud")
    mocker.patch("cloud.get_registration_token")
    payload["action"] = "completed"
    payload["workflow_job"]["runner_name"] = "some-runner"
    response = client.post("/actions/", json=payload)
    assert response.status_code == 200
    job.cloud.provision_vm.assert_not_called()
    job.cloud.destroy_vm.assert_called_once()

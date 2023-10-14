import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import main


client = TestClient(main.app)


@pytest.fixture(scope="module")
def payload():
    tests_dir = Path(__file__).absolute().parent
    return json.load(open(tests_dir / "test_payload.json"))


@pytest.mark.parametrize("action", ["queued", "completed"])
def test_post_actions(payload, mocker, action):
    mocker.patch("main.get_registration_token")
    mocker.patch("main.provision_vm")
    mocker.patch("main.destroy_vm")
    payload["action"] = action
    response = client.post("/actions/", json=payload)
    assert response.status_code == 200
    if action == "queued":
        main.get_registration_token.assert_called_once()
        main.provision_vm.assert_called_once()
    if action == "completed":
        main.destroy_vm.assert_called_once()

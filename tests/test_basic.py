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


def test_post_actions(payload, mocker):
    mocker.patch("main.get_registration_token")
    mocker.patch("main.provision_vm")
    response = client.post("/actions/", json=payload)
    assert response.status_code == 200
    main.get_registration_token.assert_called_once()
    main.provision_vm.assert_called_once()

from tests.testutils import mailing_list_url
import json
import pytest


def test_post_email_address(client):
    header = {"content-type": "application/json"}
    r = client.post("{}".format(mailing_list_url),
                    data=json.dumps({
                        "email_address": "test@platelet.app"
                    }),
                    headers=header
                    )

    assert r.status_code == 201


@pytest.mark.parametrize("login_role", ["admin"])
def test_delete_email_address(client, login_header):
    header = {"content-type": "application/json"}
    r = client.post("{}".format(mailing_list_url),
                    data=json.dumps({
                        "email_address": "test2@platelet.app"
                    }),
                    headers=header
                    )

    assert r.status_code == 201
    r2 = client.delete("{}".format(mailing_list_url),
                    data=json.dumps({
                        "email_address": "test2@platelet.app"
                    }),
                    headers=login_header
                    )

    assert r2.status_code == 202

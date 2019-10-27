def test_ping(client):
    res = client.get('/api/v0.1/ping')
    assert res.status == "200 OK"
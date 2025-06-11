from datetime import datetime, timezone, timedelta

def test_generate_token(utils_module):
    utils, fake = utils_module
    token = utils.generate_token('req1', 'proj')
    assert token is not None
    tokens = fake.tables.get('tokens')
    assert len(tokens) == 1
    rec = tokens[0]
    assert rec['shift_request_id'] == 'req1'
    assert rec['token'] == token
    assert rec['used'] is False
    expires_at = datetime.fromisoformat(rec['expires_at'])
    expected = datetime.now(timezone.utc) + timedelta(hours=24)
    assert abs((expires_at - expected).total_seconds()) < 5

def test_verify_token_and_expiry(utils_module):
    utils, fake = utils_module
    token = utils.generate_token('abc', 'proj')
    assert utils.verify_token(token, 'proj') == 'abc'
    fake.tables['tokens'][0]['used'] = True
    assert utils.verify_token(token, 'proj') is None
    fake.tables['tokens'][0]['used'] = False
    fake.tables['tokens'][0]['expires_at'] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    assert utils.verify_token(token, 'proj') is None

def test_mark_token_as_used(utils_module):
    utils, fake = utils_module
    token = utils.generate_token('xyz', 'proj')
    assert utils.mark_token_as_used(token, 'proj') is True
    assert fake.tables['tokens'][0]['used'] is True

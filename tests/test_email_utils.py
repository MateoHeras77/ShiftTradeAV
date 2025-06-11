class FakeSMTP:
    def __init__(self, *args, **kwargs):
        self.sent = []
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def starttls(self):
        pass
    def login(self, user, pwd):
        pass
    def sendmail(self, sender, recipient, msg):
        self.sent.append(msg)


def test_send_email(utils_module, monkeypatch):
    utils, _ = utils_module
    smtp = FakeSMTP()
    monkeypatch.setattr(utils.smtplib, 'SMTP', lambda s, p: smtp)
    utils.send_email('to@test.com', 'Hello', 'Body content')
    assert len(smtp.sent) == 1
    message = smtp.sent[0]
    assert 'Subject: Hello' in message
    assert 'Body content' in message


def test_send_email_with_calendar(utils_module, monkeypatch):
    utils, _ = utils_module
    smtp = FakeSMTP()
    monkeypatch.setattr(utils.smtplib, 'SMTP', lambda s, p: smtp)
    shift = {
        'id': '1',
        'flight_number': 'AV255',
        'date_request': '2024-01-01',
        'requester_name': 'A',
        'cover_name': 'B',
        'supervisor_name': 'C'
    }
    utils.send_email_with_calendar('to@test.com', 'Calendar', 'Content', shift, is_for_requester=False)
    assert len(smtp.sent) == 1
    message = smtp.sent[0]
    assert 'Subject: Calendar' in message
    assert 'text/calendar' in message

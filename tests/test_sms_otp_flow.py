from otp_auth import OtpSession


def test_issue_and_verify_local_otp():
    session = OtpSession()
    code = session.issue("9876543210")

    assert code == session.code
    assert len(code) == 6
    assert session.verify("9876543210", code) == (True, "Login successful.")

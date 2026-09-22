from app.verification.verifier import (
    VerificationStatus,
    Verifier,
)


def test_verified():

    verifier = Verifier()

    result = verifier.verify(
        expected="SUBMITTED",
        actual="SUBMITTED",
        evidence="server_status",
    )

    assert result == VerificationStatus.VERIFIED


def test_failed():

    verifier = Verifier()

    result = verifier.verify(
        expected="SUBMITTED",
        actual="DRAFT",
        evidence="server_status",
    )

    assert result == VerificationStatus.FAILED


def test_unverified():

    verifier = Verifier()

    result = verifier.verify(
        expected="SUBMITTED",
        actual="SUBMITTED",
        evidence=None,
    )

    assert result == VerificationStatus.UNVERIFIED
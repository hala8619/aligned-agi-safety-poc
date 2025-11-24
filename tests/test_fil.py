"""
tests/test_fil.py

Tests for FIL signing and verification.

FIL 署名と検証のテスト。
"""

from __future__ import annotations

import hashlib

from aligned_agi import FIL_VALUES, fil_blob, fil_signature, verify_fil_hash


def test_fil_verification_ok() -> None:
    """Verification should succeed for original FIL."""
    assert verify_fil_hash(fil_blob, fil_signature)


def test_fil_verification_detects_modification() -> None:
    """Detect modification when verifying FIL."""
    # Modify the blob by appending a string
    modified_blob = ("\n".join(FIL_VALUES) + "\nmodified").encode("utf-8")
    modified_sig = hashlib.sha256(modified_blob).digest()
    assert not verify_fil_hash(modified_blob, fil_signature)
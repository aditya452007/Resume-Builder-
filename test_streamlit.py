# python
import base64
import re
import pytest

from stream_2 import sanitize_filename, validate_inputs, generate_pdf_from_markdown


def test_sanitize_filename_basic_and_edge_cases():
    assert sanitize_filename("John Doe") == "John_Doe"
    assert sanitize_filename("  ") == "resume"
    # Apostrophes are removed, hyphens preserved, spaces replaced by underscores
    assert sanitize_filename("Ann-Marie O'Neil") == "Ann-Marie_ONeil"
    # dots and dashes kept
    assert sanitize_filename("Dr. Jane-Doe") == "Dr._Jane-Doe"


def test_validate_inputs_valid_and_invalid():
    # valid inputs -> no errors
    valid = validate_inputs("1234567890", "test@example.com", "https://linkedin.com/in/john", "https://github.com/user")
    assert isinstance(valid, list)
    assert valid == []

    # invalid inputs -> errors present
    errs = validate_inputs("123", "bad-email", "linkedin", "ftp://site")
    assert isinstance(errs, list)
    # Expect at least one of each relevant message substring
    assert any("Phone number" in e or "phone" in e.lower() for e in errs)
    assert any("valid email" in e.lower() for e in errs)
    assert any("LinkedIn" in e for e in errs)
    assert any("Portfolio/GitHub" in e or "Portfolio" in e for e in errs)


def test_generate_pdf_from_markdown_basic():
    md = """# Test Resume
This is a simple paragraph describing the candidate.

- Developed features
- Improved performance
"""
    pdf_str = generate_pdf_from_markdown(md)
    # The app later calls pdf_str.encode('latin-1'), so ensure it's a str
    assert isinstance(pdf_str, str)
    assert len(pdf_str) > 50  # simple sanity: some content exists

    # Ensure encoding to latin-1 and base64 encoding works (as stream_2 does)
    try:
        b = pdf_str.encode("latin-1")
        b64 = base64.b64encode(b)
        assert isinstance(b64, (bytes, bytearray))
    except UnicodeEncodeError:
        pytest.fail("pdf_str.encode('latin-1') raised UnicodeEncodeError for basic markdown")


def test_generate_pdf_unicode_handling_and_encoding():
    md = "## Summary\nLed a team — delivered 100% growth. “Exceeded” goals. 😊\n"
    pdf_str = generate_pdf_from_markdown(md)
    assert isinstance(pdf_str, str)

    # The app expects to call .encode('latin-1') without crashing.
    try:
        encoded = pdf_str.encode("latin-1")
        assert isinstance(encoded, (bytes, bytearray))
    except UnicodeEncodeError:
        pytest.fail("pdf_str.encode('latin-1') failed for unicode-containing markdown")


def test_pdf_streamlit_download_compatibility():
    md = "# Title\nContent line\n"
    pdf_str = generate_pdf_from_markdown(md)

    # Emulate stream_2 download and iframe creation steps
    try:
        bytes_data = pdf_str.encode("latin-1")
    except Exception as e:
        pytest.fail(f"Encoding to latin-1 failed: {e}")

    try:
        base64_pdf = base64.b64encode(bytes_data).decode("utf-8")
        iframe = f'data:application/pdf;base64,{base64_pdf}'
        assert iframe.startswith("data:application/pdf;base64,")
    except Exception as e:
        pytest.fail(f"Base64 encoding or iframe creation failed: {e}")
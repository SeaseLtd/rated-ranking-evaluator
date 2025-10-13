from rre_tools.core.utils import clean_text


def test_clean_text__expects__removes_html_unescapes_and_collapses_ws():
    raw = "  Hello &lt;b&gt;World&lt;/b&gt;  and  &amp;amp; test  "
    cleaned = clean_text(raw)
    assert cleaned == "Hello World and &amp; test"


def test_clean_text__expects__nfkc_and_control_char_removal():
    raw = "ＡＢＣ １２３\u0007"  # control char
    cleaned = clean_text(raw)
    assert cleaned == "ABC 123"


def test_clean_text__expects__be_conservative_by_default():
    a = "Hello World"
    b = "hello world"
    # By default (lowercase=False), keys differ
    assert clean_text(a) != clean_text(b)

def test_clean_text__expects__preserves_accent_and_punct():
    accented = "café?"
    plain = "cafe"

    # Defaults keep accents and punctuation → keys should differ
    assert clean_text(accented) != clean_text(plain)
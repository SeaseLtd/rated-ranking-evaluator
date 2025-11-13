from rre_tools.shared.search_engines import BaseSearchEngine


def test_escape_no_special_chars():
    assert BaseSearchEngine.escape("hello world") == "hello world"

def test_escape_basic_specials():
    assert BaseSearchEngine.escape("a+b") == "a\\+b"
    assert BaseSearchEngine.escape("field:value") == "field\\:value"
    assert BaseSearchEngine.escape("(test)") == "\\(test\\)"

def test_escape_multiple_specials():
    assert BaseSearchEngine.escape("a+b-(c*d)?") == "a\\+b\\-\\(c\\*d\\)\\?"
    assert BaseSearchEngine.escape("[range]~{json}") == "\\[range\\]\\~\\{json\\}"

def test_escape_with_backslash():
    assert BaseSearchEngine.escape("path\\to/file") == "path\\\\to\\/file"

def test_escape_quotes():
    assert BaseSearchEngine.escape('"phrase" AND title:book') == '\\"phrase\\" AND title\\:book'

def test_escape_all_special_chars():
    all_specials = r'\+-!():^[]"{}~*?|&/'
    expected = ''.join(['\\' + c for c in all_specials])
    assert BaseSearchEngine.escape(all_specials) == expected

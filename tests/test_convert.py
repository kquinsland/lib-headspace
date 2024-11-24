"""Sanity check the JS -> Python conversion function."""

from src.lib_headspace.api.util.convert import env_js_to_python


def test_basic_conversion():
    """Most basic case: key/value get double quotes"""
    js_text = """
    window.HEADSPACE_APP_CONFIG = {
        key: 'value'
    };
    document.getElementById('env_config').remove();
    """
    expected_output = {"key": "value"}
    assert env_js_to_python(js_text) == expected_output


def test_backticks_conversion():
    """Backticks are converted to double quotes"""
    js_text = """
    window.HEADSPACE_APP_CONFIG = {
        key: `value`
    };
    document.getElementById('env_config').remove();
    """
    expected_output = {"key": "value"}
    assert env_js_to_python(js_text) == expected_output


def test_dom_manipulation_removal():
    """Make sure the JS not related to the config object is removed:"""
    js_text = """
    window.HEADSPACE_APP_CONFIG = {
        key: 'value'
    };
    document.getElementById('env_config').remove();
    """
    expected_output = {"key": "value"}
    assert env_js_to_python(js_text) == expected_output


def test_trailing_commas_removal():
    """JS allows trailing commas. Python does, too, technically, but not on dictionaries"""
    js_text = """
    window.HEADSPACE_APP_CONFIG = {
        key1: 'value1',
        key2: 'value2',
    };
    document.getElementById('env_config').remove();
    """
    expected_output = {"key1": "value1", "key2": "value2"}
    assert env_js_to_python(js_text) == expected_output

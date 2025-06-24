"""
Unit tests for MistHelper utility functions.

- Tests flattening, escaping, CSV writing, and key extraction helpers.
- Uses unittest standard library.
- Requires MistHelper.MistHelper module.
"""

import unittest  # Who: Python standard library; What: Provides unit testing framework; When: Used throughout; Where: Top of file; Why: To define and run tests
import os  # Who: Python standard library; What: OS interface; When: Used for file operations; Where: Top of file; Why: To check and remove test files
import csv  # Who: Python standard library; What: CSV file operations; When: Used for reading/writing CSVs; Where: Top of file; Why: To verify CSV output
from MistHelper.MistHelper import (  # Who: MistHelper module author; What: Imports utility functions; When: At import time; Where: Top of file; Why: To test these functions
    flatten_dict_recursively,
    flatten_nested_fields_in_list,
    escape_multiline_strings_for_csv,
    write_dict_list_to_csv,
    convert_list_values_to_csv_strings,
    get_all_unique_dict_keys
)

class TestMistHelperUtils(unittest.TestCase):
    """Unit tests for MistHelper utility functions."""

    def test_flatten_dict_recursively(self):
        """
        Who: Test author (jmorrison or contributor)
        What: Tests flatten_dict_recursively with nested dict and list.
        When: During unit test execution.
        Where: In the test suite for MistHelper utilities.
        Why: To verify that nested dictionaries and lists are properly flattened.
        """
        nested = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}, 'f': [1, 2, 3]}  # Test input: nested dict
        flat = flatten_dict_recursively(nested)  # Call function under test
        self.assertEqual(flat['a'], 1)  # Check flat key 'a'
        self.assertEqual(flat['b_c'], 2)  # Check nested flattening
        self.assertEqual(flat['b_d_e'], 3)  # Check deep flattening
        self.assertEqual(flat['f'], '1,2,3')  # Check list flattening

    def test_flatten_dict_recursively_empty(self):  # Tests empty dict input
        """Test flatten_dict_recursively with empty dict."""
        self.assertEqual(flatten_dict_recursively({}), {})

    def test_flatten_dict_recursively_mixed_list(self):  # Tests list with dict inside
        """Test flatten_dict_recursively with list containing dict."""
        d = {'a': [1, {'b': 2}, 3]}
        flat = flatten_dict_recursively(d)
        # Should join as string, not flatten dict inside list
        self.assertIn('a', flat)
        self.assertTrue("{'b': 2}" in flat['a'] or '{"b": 2}' in flat['a'])

    def test_flatten_dict_recursively_deep(self):  # Tests deep nesting
        """Test flatten_dict_recursively with deep nesting."""
        d = {'a': {'b': {'c': {'d': 1}}}}
        flat = flatten_dict_recursively(d)
        self.assertEqual(flat['a_b_c_d'], 1)

    def test_flatten_nested_fields_in_list(self):  # Tests flattening in list of dicts
        """Test flatten_nested_fields_in_list with nested dicts and lists."""
        data = [
            {'a': {'b': 1}, 'c': [2, 3]},
            {'a': {'b': 2}, 'c': [4, 5]}
        ]
        flat = flatten_nested_fields_in_list(data)
        self.assertIn('a_b', flat[0])
        self.assertEqual(flat[0]['a_b'], 1)
        self.assertEqual(flat[1]['a_b'], 2)
        self.assertEqual(flat[0]['c'], '2,3')

    def test_flatten_nested_fields_in_list_empty(self):  # Tests empty list and dict
        """Test flatten_nested_fields_in_list with empty list and dict."""
        self.assertEqual(flatten_nested_fields_in_list([]), [])
        self.assertEqual(flatten_nested_fields_in_list([{}]), [{}])

    def test_flatten_nested_fields_in_list_malformed_string(self):  # Tests malformed string input
        """Test flatten_nested_fields_in_list with malformed stringified dict."""
        data = [{'a': "{'x': 1, 'y': 2"}]  # missing closing brace
        flat = flatten_nested_fields_in_list(data)
        self.assertEqual(flat[0]['a'], "{'x': 1, 'y': 2")

    def test_flatten_nested_fields_in_list_stringified_list_of_dicts(self):  # Tests stringified list of dicts
        """Test flatten_nested_fields_in_list with stringified list of dicts."""
        data = [{'a': "[{'x': 1}, {'y': 2}]"}]
        flat = flatten_nested_fields_in_list(data)
        self.assertIn('a_0_x', flat[0])
        self.assertIn('a_1_y', flat[0])
        self.assertEqual(flat[0]['a_0_x'], 1)
        self.assertEqual(flat[0]['a_1_y'], 2)

    def test_escape_multiline_strings_for_csv(self):  # Tests escaping newlines
        """Test escape_multiline_strings_for_csv with newlines."""
        data = [{'a': 'line1\nline2', 'b': 'no_newline', 'c': ['x', 'y']}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertEqual(escaped[0]['a'], 'line1\\nline2')
        self.assertEqual(escaped[0]['b'], 'no_newline')
        self.assertEqual(escaped[0]['c'], 'x,y')

    def test_escape_multiline_strings_for_csv_carriage_return(self):  # Tests carriage return removal
        """Test escape_multiline_strings_for_csv with carriage returns."""
        data = [{'a': 'line1\rline2'}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertEqual(escaped[0]['a'], 'line1line2')

    def test_escape_multiline_strings_for_csv_list_with_newlines(self):  # Tests list with newlines
        """Test escape_multiline_strings_for_csv with list containing newlines."""
        data = [{'a': ['x\n', 'y\r']}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertEqual(escaped[0]['a'], 'x\n,y\r')

    def test_convert_list_values_to_csv_strings_nested(self):  # Tests nested lists
        """Test convert_list_values_to_csv_strings with nested lists."""
        data = [{'a': [[1, 2], [3, 4]], 'b': [5, 6]}]
        converted = convert_list_values_to_csv_strings(data)
        self.assertEqual(converted[0]['a'], '[1, 2],[3, 4]')
        self.assertEqual(converted[0]['b'], '5,6')

    def test_convert_list_values_to_csv_strings_non_list(self):  # Tests non-list values
        """Test convert_list_values_to_csv_strings with non-list values."""
        data = [{'a': 'notalist', 'b': 123}]
        converted = convert_list_values_to_csv_strings(data)
        self.assertEqual(converted[0]['a'], 'notalist')
        self.assertEqual(converted[0]['b'], 123)

    def test_get_all_unique_dict_keys_non_string(self):  # Tests non-string dict keys
        """Test get_all_unique_dict_keys with non-string keys."""
        data = [{1: 'a', 'b': 2}, {'c': 3, 2: 4}]
        keys = get_all_unique_dict_keys(data)
        self.assertEqual(set(keys), {'1', '2', 'b', 'c'})

    def test_get_all_unique_dict_keys_empty(self):  # Tests empty input
        """Test get_all_unique_dict_keys with empty input."""
        self.assertEqual(get_all_unique_dict_keys([]), [])

    def test_write_dict_list_to_csv(self):  # Tests writing to CSV
        """Test write_dict_list_to_csv with normal data."""
        data = [
            {'a': 1, 'b': 'foo'},
            {'a': 2, 'b': 'bar'}
        ]
        filename = 'test_output.csv'
        write_dict_list_to_csv(data, filename)
        self.assertTrue(os.path.exists(filename))
        with open(filename, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 2)
            self.assertEqual(reader[0]['a'], '1')
            self.assertEqual(reader[1]['b'], 'bar')
        os.remove(filename)

    def test_write_dict_list_to_csv_missing_fields(self):  # Tests missing fields in rows
        """Test write_dict_list_to_csv with missing fields in rows."""
        data = [{'a': 1}, {'b': 2}]
        filename = 'test_missing_fields.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 2)
            self.assertIn('a', reader[0])
            self.assertIn('b', reader[1])
        os.remove(filename)

    def test_write_dict_list_to_csv_special_chars(self):  # Tests special characters in CSV
        """Test write_dict_list_to_csv with special characters."""
        data = [{'a': 'hello,world', 'b': 'foo\nbar'}]
        filename = 'test_special_chars.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('hello,world', content)
            self.assertIn('foo\\nbar', content)
        os.remove(filename)

    def test_flatten_dict_recursively_non_string_keys(self):  # Tests non-string keys in flatten
        """Test flatten_dict_recursively with non-string keys."""
        d = {1: 'a', (2, 3): {'b': 4}}
        flat = flatten_dict_recursively(d)
        self.assertIn('1', flat)
        self.assertIn('(2, 3)_b', flat)
        self.assertEqual(flat['1'], 'a')
        self.assertEqual(flat['(2, 3)_b'], 4)

    def test_flatten_dict_recursively_none_and_bool(self):  # Tests None and bool values
        """Test flatten_dict_recursively with None and bool values."""
        d = {'a': None, 'b': True, 'c': False}
        flat = flatten_dict_recursively(d)
        self.assertEqual(flat['a'], None)
        self.assertEqual(flat['b'], True)
        self.assertEqual(flat['c'], False)

    def test_flatten_nested_fields_in_list_mixed_types(self):  # Tests mixed types in list
        """Test flatten_nested_fields_in_list with mixed types in list."""
        data = [{'a': 1}, 'notadict', {'b': 2}]
        flat = flatten_nested_fields_in_list([x for x in data if isinstance(x, dict)])
        self.assertEqual(flat[0]['a'], 1)
        self.assertEqual(flat[1]['b'], 2)

    def test_flatten_nested_fields_in_list_json_string(self):  # Tests JSON string input
        """Test flatten_nested_fields_in_list with JSON string input."""
        data = [{'a': '"just a string"'}]
        flat = flatten_nested_fields_in_list(data)
        self.assertEqual(flat[0]['a'], '"just a string"')

    def test_flatten_nested_fields_in_list_empty_and_none(self):  # Tests empty and None values
        """Test flatten_nested_fields_in_list with empty and None values."""
        data = [{'a': ''}, {'b': None}, {'c': False}]
        flat = flatten_nested_fields_in_list(data)
        self.assertEqual(flat[0]['a'], '')
        self.assertIsNone(flat[1]['b'])
        self.assertFalse(flat[2]['c'])

    def test_escape_multiline_strings_for_csv_bytes(self):  # Tests bytes input
        """Test escape_multiline_strings_for_csv with bytes input."""
        data = [{'a': b'bytes'}]
        # Should not crash, should leave as is
        try:
            escaped = escape_multiline_strings_for_csv(data)
            self.assertEqual(escaped[0]['a'], b'bytes')
        except Exception as e:
            self.fail(f"escape_multiline_strings_for_csv failed on bytes: {e}")

    def test_escape_multiline_strings_for_csv_already_escaped(self):  # Tests already escaped string
        """Test escape_multiline_strings_for_csv with already escaped string."""
        data = [{'a': 'foo\\nbar'}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertEqual(escaped[0]['a'], 'foo\\nbar')

    def test_escape_multiline_strings_for_csv_unicode(self):  # Tests unicode characters
        """Test escape_multiline_strings_for_csv with unicode characters."""
        data = [{'a': 'hello\n😊'}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertIn('😊', escaped[0]['a'])
        self.assertIn('\\n', escaped[0]['a'])

    def test_convert_list_values_to_csv_strings_tuple_set(self):  # Tests tuple and set
        """Test convert_list_values_to_csv_strings with tuple and set."""
        data = [{'a': (1, 2), 'b': {3, 4}}]
        converted = convert_list_values_to_csv_strings(data)
        self.assertEqual(converted[0]['a'], '1,2')
        # set order is not guaranteed
        self.assertTrue(converted[0]['b'] in ['3,4', '4,3'])

    def test_convert_list_values_to_csv_strings_deeply_nested(self):  # Tests deeply nested lists
        """Test convert_list_values_to_csv_strings with deeply nested lists."""
        data = [{'a': [[[1]]]}]
        converted = convert_list_values_to_csv_strings(data)
        self.assertEqual(converted[0]['a'], '[[1]]')

    def test_get_all_unique_dict_keys_overlap_types(self):  # Tests overlapping key types
        """Test get_all_unique_dict_keys with overlapping key types."""
        data = [{1: 'a'}, {'1': 'b'}, {None: 'c'}, {False: 'd'}]
        keys = get_all_unique_dict_keys(data)
        self.assertIn('1', keys)
        self.assertIn('None', keys)
        self.assertIn('False', keys)

    def test_write_dict_list_to_csv_one_row_missing_fields(self):  # Tests one row with missing fields
        """Test write_dict_list_to_csv with one row missing fields."""
        data = [{'a': 1}]
        filename = 'test_one_row.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 1)
            self.assertIn('a', reader[0])
        os.remove(filename)

    def test_write_dict_list_to_csv_delimiters(self):  # Tests delimiters and quotes
        """Test write_dict_list_to_csv with delimiters and quotes."""
        data = [{'a': 'a, b', 'b': '"quoted"', 'c': 'line1\nline2'}]
        filename = 'test_delimiters.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('"a, b"', content)
            self.assertIn('"quoted"', content)
            self.assertIn('line1\\nline2', content)
        os.remove(filename)

    def test_write_dict_list_to_csv_large_value(self):  # Tests large value in CSV
        """Test write_dict_list_to_csv with large value."""
        data = [{'a': 'x' * 10000}]
        filename = 'test_large_value.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('x' * 1000, content)
        os.remove(filename)

if __name__ == '__main__':  # Who: Python interpreter; What: Entry point; When: Script run; Where: Bottom; Why: To run tests
    unittest.main()  # Run all tests

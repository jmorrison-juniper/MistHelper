import unittest
import os
import csv
from MistHelper.MistHelper import (flatten_dict_recursively,
                                    flatten_nested_fields_in_list,
                                    escape_multiline_strings_for_csv,
                                    write_dict_list_to_csv,
                                    convert_list_values_to_csv_strings,
                                    get_all_unique_dict_keys)

class TestMistHelperUtils(unittest.TestCase):
    def test_flatten_dict_recursively(self):
        nested = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}, 'f': [1, 2, 3]}
        flat = flatten_dict_recursively(nested)
        self.assertEqual(flat['a'], 1)
        self.assertEqual(flat['b_c'], 2)
        self.assertEqual(flat['b_d_e'], 3)
        self.assertEqual(flat['f'], '1,2,3')

    def test_flatten_dict_recursively_empty(self):
        self.assertEqual(flatten_dict_recursively({}), {})

    def test_flatten_dict_recursively_mixed_list(self):
        d = {'a': [1, {'b': 2}, 3]}
        flat = flatten_dict_recursively(d)
        # Should join as string, not flatten dict inside list
        self.assertIn('a', flat)
        self.assertTrue("{'b': 2}" in flat['a'] or '{"b": 2}' in flat['a'])

    def test_flatten_dict_recursively_deep(self):
        d = {'a': {'b': {'c': {'d': 1}}}}
        flat = flatten_dict_recursively(d)
        self.assertEqual(flat['a_b_c_d'], 1)

    def test_flatten_nested_fields_in_list(self):
        data = [
            {'a': {'b': 1}, 'c': [2, 3]},
            {'a': {'b': 2}, 'c': [4, 5]}
        ]
        flat = flatten_nested_fields_in_list(data)
        self.assertIn('a_b', flat[0])
        self.assertEqual(flat[0]['a_b'], 1)
        self.assertEqual(flat[1]['a_b'], 2)
        self.assertEqual(flat[0]['c'], '2,3')

    def test_flatten_nested_fields_in_list_empty(self):
        self.assertEqual(flatten_nested_fields_in_list([]), [])
        self.assertEqual(flatten_nested_fields_in_list([{}]), [{}])

    def test_flatten_nested_fields_in_list_malformed_string(self):
        data = [{'a': "{'x': 1, 'y': 2"}]  # missing closing brace
        flat = flatten_nested_fields_in_list(data)
        self.assertEqual(flat[0]['a'], "{'x': 1, 'y': 2")

    def test_flatten_nested_fields_in_list_stringified_list_of_dicts(self):
        data = [{'a': "[{'x': 1}, {'y': 2}]"}]
        flat = flatten_nested_fields_in_list(data)
        self.assertIn('a_0_x', flat[0])
        self.assertIn('a_1_y', flat[0])
        self.assertEqual(flat[0]['a_0_x'], 1)
        self.assertEqual(flat[0]['a_1_y'], 2)

    def test_escape_multiline_strings_for_csv(self):
        data = [{'a': 'line1\nline2', 'b': 'no_newline', 'c': ['x', 'y']}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertEqual(escaped[0]['a'], 'line1\\nline2')
        self.assertEqual(escaped[0]['b'], 'no_newline')
        self.assertEqual(escaped[0]['c'], 'x,y')

    def test_escape_multiline_strings_for_csv_carriage_return(self):
        data = [{'a': 'line1\rline2'}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertEqual(escaped[0]['a'], 'line1line2')

    def test_escape_multiline_strings_for_csv_list_with_newlines(self):
        data = [{'a': ['x\n', 'y\r']}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertEqual(escaped[0]['a'], 'x\n,y\r')

    def test_convert_list_values_to_csv_strings_nested(self):
        data = [{'a': [[1, 2], [3, 4]], 'b': [5, 6]}]
        converted = convert_list_values_to_csv_strings(data)
        self.assertEqual(converted[0]['a'], '[1, 2],[3, 4]')
        self.assertEqual(converted[0]['b'], '5,6')

    def test_convert_list_values_to_csv_strings_non_list(self):
        data = [{'a': 'notalist', 'b': 123}]
        converted = convert_list_values_to_csv_strings(data)
        self.assertEqual(converted[0]['a'], 'notalist')
        self.assertEqual(converted[0]['b'], 123)

    def test_get_all_unique_dict_keys_non_string(self):
        data = [{1: 'a', 'b': 2}, {'c': 3, 2: 4}]
        keys = get_all_unique_dict_keys(data)
        self.assertEqual(set(keys), {'1', '2', 'b', 'c'})

    def test_get_all_unique_dict_keys_empty(self):
        self.assertEqual(get_all_unique_dict_keys([]), [])

    def test_write_dict_list_to_csv(self):
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

    def test_write_dict_list_to_csv_missing_fields(self):
        data = [{'a': 1}, {'b': 2}]
        filename = 'test_missing_fields.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 2)
            self.assertIn('a', reader[0])
            self.assertIn('b', reader[1])
        os.remove(filename)

    def test_write_dict_list_to_csv_special_chars(self):
        data = [{'a': 'hello,world', 'b': 'foo\nbar'}]
        filename = 'test_special_chars.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('hello,world', content)
            self.assertIn('foo\\nbar', content)
        os.remove(filename)

    def test_flatten_dict_recursively_non_string_keys(self):
        d = {1: 'a', (2, 3): {'b': 4}}
        flat = flatten_dict_recursively(d)
        self.assertIn('1', flat)
        self.assertIn('(2, 3)_b', flat)
        self.assertEqual(flat['1'], 'a')
        self.assertEqual(flat['(2, 3)_b'], 4)

    def test_flatten_dict_recursively_none_and_bool(self):
        d = {'a': None, 'b': True, 'c': False}
        flat = flatten_dict_recursively(d)
        self.assertEqual(flat['a'], None)
        self.assertEqual(flat['b'], True)
        self.assertEqual(flat['c'], False)

    def test_flatten_nested_fields_in_list_mixed_types(self):
        data = [{'a': 1}, 'notadict', {'b': 2}]
        flat = flatten_nested_fields_in_list([x for x in data if isinstance(x, dict)])
        self.assertEqual(flat[0]['a'], 1)
        self.assertEqual(flat[1]['b'], 2)

    def test_flatten_nested_fields_in_list_json_string(self):
        data = [{'a': '"just a string"'}]
        flat = flatten_nested_fields_in_list(data)
        self.assertEqual(flat[0]['a'], '"just a string"')

    def test_flatten_nested_fields_in_list_empty_and_none(self):
        data = [{'a': ''}, {'b': None}, {'c': False}]
        flat = flatten_nested_fields_in_list(data)
        self.assertEqual(flat[0]['a'], '')
        self.assertIsNone(flat[1]['b'])
        self.assertFalse(flat[2]['c'])

    def test_escape_multiline_strings_for_csv_bytes(self):
        data = [{'a': b'bytes'}]
        # Should not crash, should leave as is
        try:
            escaped = escape_multiline_strings_for_csv(data)
            self.assertEqual(escaped[0]['a'], b'bytes')
        except Exception as e:
            self.fail(f"escape_multiline_strings_for_csv failed on bytes: {e}")

    def test_escape_multiline_strings_for_csv_already_escaped(self):
        data = [{'a': 'foo\\nbar'}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertEqual(escaped[0]['a'], 'foo\\nbar')

    def test_escape_multiline_strings_for_csv_unicode(self):
        data = [{'a': 'hello\n😊'}]
        escaped = escape_multiline_strings_for_csv(data)
        self.assertIn('😊', escaped[0]['a'])
        self.assertIn('\\n', escaped[0]['a'])

    def test_convert_list_values_to_csv_strings_tuple_set(self):
        data = [{'a': (1, 2), 'b': {3, 4}}]
        converted = convert_list_values_to_csv_strings(data)
        self.assertEqual(converted[0]['a'], '1,2')
        # set order is not guaranteed
        self.assertTrue(converted[0]['b'] in ['3,4', '4,3'])

    def test_convert_list_values_to_csv_strings_deeply_nested(self):
        data = [{'a': [[[1]]]}]
        converted = convert_list_values_to_csv_strings(data)
        self.assertEqual(converted[0]['a'], '[[1]]')

    def test_get_all_unique_dict_keys_overlap_types(self):
        data = [{1: 'a'}, {'1': 'b'}, {None: 'c'}, {False: 'd'}]
        keys = get_all_unique_dict_keys(data)
        self.assertIn('1', keys)
        self.assertIn('None', keys)
        self.assertIn('False', keys)

    def test_write_dict_list_to_csv_one_row_missing_fields(self):
        data = [{'a': 1}]
        filename = 'test_one_row.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 1)
            self.assertIn('a', reader[0])
        os.remove(filename)

    def test_write_dict_list_to_csv_delimiters(self):
        data = [{'a': 'a, b', 'b': '"quoted"', 'c': 'line1\nline2'}]
        filename = 'test_delimiters.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('"a, b"', content)
            self.assertIn('"quoted"', content)
            self.assertIn('line1\\nline2', content)
        os.remove(filename)

    def test_write_dict_list_to_csv_large_value(self):
        data = [{'a': 'x' * 10000}]
        filename = 'test_large_value.csv'
        write_dict_list_to_csv(data, filename)
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('x' * 1000, content)
        os.remove(filename)

if __name__ == '__main__':
    unittest.main()

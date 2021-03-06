import numpy as np
import unittest

from hdfaccess.parameter import MappedArray, Parameter


class TestMappedArray(unittest.TestCase):
    mapping = {1: 'one', 2: 'two', 3: 'three'}

    def test_any_of(self):
        values = [1, 2, 3, 2, 1, 2, 3, 2, 1]
        a = MappedArray(values, mask=[True] + [False] * 8,
                        values_mapping=self.mapping)
        result = a.any_of('one', 'three')
        self.assertEqual(
            result.tolist(),
            [None, False, True, False, True, False, True, False, True])
        self.assertRaises(ValueError, a.any_of, 'one', 'invalid')
        result = a.any_of('one', 'invalid', ignore_missing=True)
        self.assertEqual(
            result.tolist(),
            [None, False, False, False, True, False, False, False, True],
        )

    def test_create_from_list(self):
        values = [1, 2, 3]
        mask = [False, True, False]
        a = MappedArray(values, mask=mask, values_mapping=self.mapping)
        self.assertEqual(a[0], 'one')
        self.assertTrue(a[1] is np.ma.masked)
        self.assertEqual(a[2], 'three')

    def test_create_from_ma(self):
        values = [1, 2, 3]
        mask = [False, True, False]
        arr = np.ma.MaskedArray(values, mask)
        a = MappedArray(arr, values_mapping=self.mapping)
        self.assertEqual(a[0], 'one')
        self.assertTrue(a[1] is np.ma.masked)
        self.assertEqual(a[2], 'three')

    def test_get_slice(self):
        values = [1, 2, 3]
        mask = [False, True, False]
        arr = np.ma.MaskedArray(values, mask)
        a = MappedArray(arr, values_mapping=self.mapping)
        a = a[:2]
        self.assertEqual(a[0], 'one')
        self.assertTrue(a[1] is np.ma.masked)
        # get mapped data value
        self.assertEqual(type(a), MappedArray)
        self.assertEqual(a.state['one'], 1)

    def test_set_slice(self):
        values = [1, 2, 3, 3]
        mask = [False, True, False, True]
        arr = np.ma.MaskedArray(values, mask)
        a = MappedArray(arr, values_mapping=self.mapping)
        a[:2] = ['two', 'three']  # this will unmask second item!
        self.assertEqual(a[0], 'two')
        self.assertEqual(list(a.raw), [2, 3, 3, np.ma.masked])
        self.assertEqual(a[1], 'three')  # updated value
        self.assertTrue(a[1] is not np.ma.masked)  # mask is lost
        self.assertTrue(a[3] is np.ma.masked)  # mask is maintained

        a.mask = False
        a[:3] = np.ma.masked
        self.assertEqual(list(a.raw.mask), [True, True, True, False])
        a[:] = np.ma.array([3, 3, 3, 3], mask=[False, False, True, True])
        self.assertEqual(list(a.raw.mask), [False, False, True, True])
        # set a slice to a single value
        a[2:] = 'one'
        self.assertEqual(list(a.raw.data[2:]), [1, 1])
        a[2:] = 3
        self.assertEqual(list(a.raw.data[2:]), [3, 3])
        # set a slice to a single element list (odd but consistent with numpy)
        a[2:] = [2]
        self.assertEqual(list(a.raw.data[2:]), [2, 2])
        a[2:] = ['three']
        self.assertEqual(list(a.raw.data[2:]), [3, 3])
        # unequal number of arguments
        self.assertRaises(ValueError, a.__setitem__, slice(-3, None), ['one', 'one'])

    def test_no_mapping(self):
        # values_mapping is no longer a requirement. (check no exception raised)
        self.assertTrue(all(MappedArray(np.arange(10)).data == np.arange(10)))

    def test_repr(self):
        values = [1, 2, 3, 3]
        mask = [False, True, False, True]
        arr = np.ma.MaskedArray(values, mask)
        a = MappedArray(arr, values_mapping=self.mapping)
        # ensure string vals is within repr
        print a.__repr__()
        self.assertTrue('one' in a.__repr__())

    def test_getitem_filters_boolean_array(self):
        "Tests __getitem__ and __eq__ and __ne__"
        ma = MappedArray(np.ma.arange(4, -1, step=-1), values_mapping={1: 'one', 2: 'two'})

        # boolean returned where: array == value
        #                                 4       3      2     >1<     0
        self.assertEqual(list(ma == 1), [False, False, False, True, False])
        self.assertEqual(list(ma != 1), [True, True, True, False, True])

        # Nice to Have : Overide == for state
        # boolean returned where: array == 'state'
        #                                     4       3     >2<      1     0
        self.assertEqual(list(ma == 'two'), [False, False, True, False, False])
        self.assertEqual(list(ma != 'two'), [True, True, False, True, True])

        # check __repr__ and __str__ work
        self.assertEqual((ma == 'two').__str__(), '[False False  True False False]')
        self.assertEqual((ma == 'two').__repr__(), '''\
masked_array(data = [False False  True False False],
             mask = False,
       fill_value = True)
''')
        n = np.arange(5)
        self.assertEqual(list(n[ma <= 1]), [3, 4])   # last two elements in ma are <= 1

        # boolean returned where: array == 'state'
        self.assertEqual(list(ma[ma <= 1]), ['one', '?'])  # last two elements in ma are <= 1

    def test_tolist(self):
        array = MappedArray([0] * 5 + [1] * 5, values_mapping={0: '-', 1: 'Warning'})
        self.assertEqual(array.tolist(), ['-'] * 5 + ['Warning'] * 5)
        array[2] = np.ma.masked
        self.assertEqual(array.tolist(), ['-'] * 2 + [None] + ['-'] * 2 + ['Warning'] * 5)

    def test_set_item(self):
        values_mapping = {1: 'one', 2: 'two', 3: 'three', 4: 'four'}
        ma = MappedArray(np.ma.arange(1, 5), values_mapping=values_mapping)
        # Set single item.
        ma[0] = 'four'
        self.assertEqual(ma[0], 'four')
        ma[1] = 3
        self.assertEqual(ma[1], 'three')
        # Set multiple items with a list.
        ma[2:] = ['one', 'two']
        self.assertEqual(ma[2], 'one')
        self.assertEqual(ma[3], 'two')
        ma[2:] = [3, 4]
        self.assertEqual(ma[2], 'three')
        self.assertEqual(ma[3], 'four')
        # Set multiple items with a MaskedArray.
        ma[2:] = np.ma.MaskedArray([2, 3])
        self.assertEqual(ma[2], 'two')
        self.assertEqual(ma[3], 'three')
        ma[2:] = np.ma.MaskedArray([1.0, 2.0])
        self.assertEqual(ma[2], 'one')
        self.assertEqual(ma[3], 'two')
        ma[2:] = np.ma.MaskedArray([2, 3], mask=[True, False])
        self.assertTrue(ma[2] is np.ma.masked)
        self.assertEqual(ma[3], 'three')
        ma[np.array([True, False, True, True])] = np.ma.MaskedArray([4, 2, 3], mask=[False, False, True])
        self.assertEqual(ma[0], 'four')
        self.assertEqual(ma[2], 'two')
        self.assertTrue(ma[3] is np.ma.masked)
        # Set multiple items with a MappedArray.
        ma[:3] = MappedArray([1, 2, 3], values_mapping=values_mapping)
        self.assertEqual(ma[0], 'one')
        self.assertEqual(ma[1], 'two')
        self.assertEqual(ma[2], 'three')

    def test_array_equality(self):
        ma = MappedArray(np.ma.arange(1, 4), values_mapping={1: 'one', 2: 'two'})

        # unequal length arrays compared return False in np
        self.assertEqual(ma == ['one', 'two'], False)
        self.assertEqual(ma != ['one', 'two'], True)

        # mapped values
        np.testing.assert_array_equal(ma[:2] == ['one', 'two'], [True, True])
        np.testing.assert_array_equal(ma[:2] == ['one', 'one'], [True, False])
        np.testing.assert_array_equal(ma[:2] == ['INVALID', 'one'], [False, False])

        # where no mapping exists
        np.testing.assert_array_equal(ma == [1, 2, 3], [True, True, True])
        # test using dtype=int
        np.testing.assert_array_equal(ma == np.ma.array([1, 2, 3]), [True, True, True])
        # no mapping means you cannot find those values! Always get a FAIL
        # - sort out your values mapping!
        np.testing.assert_array_equal(ma == ['one', 'two', None], [True, True, False])
        np.testing.assert_array_equal(ma == ['one', 'two', '?'], [True, True, False])
        # test __ne__ (easy by comparison!)
        np.testing.assert_array_equal(ma != ['one', 'two', '?'], [False, False, True])

        # masked values
        ma[0] = np.ma.masked
        np.testing.assert_array_equal(ma[:2] == [np.ma.masked, 2], [True, True])
        # can't compare lists with numpy arrays
        np.testing.assert_array_equal(ma[:2] == [np.ma.masked, 'two'], [True, True])

    def test_array_inequality_type_and_mask(self):
        data = [0, 0, 0, 0, 1, 1, 0, 0, 1, 0]

        array = np.ma.masked_array(data=data, mask=False)
        array = MappedArray(array, values_mapping={0: 'Off', 1: 'On'})

        expected = np.ma.array([not bool(x) for x in data])

        np.testing.assert_array_equal(array != 'On', expected)

        # Ensure that __ne__ is returning a boolean array!
        np.testing.assert_array_equal(
            str(array != 'On'),
            '[True True True True False False True True False True]')

        array[array != 'On'] = np.ma.masked
        np.testing.assert_array_equal(array.mask, expected)

    def test_array_finalize(self):
        """
        Numpy in some cases creates an array derived from the arguments instead
        of modifying the original object in place.

        In those cases new_array.__array_finalize__() is called to apply all
        specific initialisations.

        In case of MappedArray it should copy values_mapping from the master
        object.
        """
        data = [0, 0, 0, 0, 1, 1, 0, 0, 1, 0]

        array = np.ma.masked_array(data=data, mask=False)
        array = MappedArray(array, values_mapping={0: 'Off', 1: 'On'})
        # if the __array_finalize__ wasn't called this would raise exception:
        # AttributeError: 'MappedArray' object has no attribute 'values_mapping'
        result = np.ma.masked_less(array, 1.0)
        self.assertEquals(array.values_mapping, result.values_mapping)


class TestParameter(unittest.TestCase):
    def test_parameter(self):
        p_name = 'param'
        p = Parameter(p_name)
        self.assertEqual(p.name, p_name)
        self.assertEqual(p.array, [])
        self.assertEqual(p.frequency, 1)
        self.assertEqual(p.offset, 0)
        self.assertEqual(p.arinc_429, None)
        array = np.ma.arange(10)
        frequency = 8
        offset = 1
        arinc_429 = True
        p = Parameter('param', array=array, frequency=frequency, offset=offset,
                      arinc_429=arinc_429)
        np.testing.assert_array_equal(p.array, array)
        self.assertEqual(p.frequency, frequency)
        self.assertEqual(p.offset, offset)
        self.assertEqual(p.arinc_429, arinc_429)

    def test_multivalue_parameter(self):
        values = [1, 2, 3]
        mask = [False, True, False]
        array = np.ma.MaskedArray(values, mask)
        mapping = {1: 'One', 2: 'Two'}
        p = Parameter('param', array=array, values_mapping=mapping)
        self.assertEqual(p.array[0], 'One')
        self.assertEqual(p.raw_array[0], 1)
        self.assertTrue(p.array[1] is np.ma.masked)
        self.assertTrue(p.raw_array[1] is np.ma.masked)
        # Get a value not in the mapping
        self.assertEqual(p.array[2], '?')
        self.assertEqual(p.raw_array[2], 3)

    def test_multivalue_parameter_float_values(self):
        values = [17.5, 10.5, 9]
        mask = [False, True, False]
        array = np.ma.MaskedArray(values, mask)
        mapping = {'17.5': 'One', 10.5: 'Two', 5: 'Three'}
        p = Parameter('param', array=array, values_mapping=mapping)
        self.assertEqual(p.array[0], 'One')
        self.assertEqual(p.raw_array[0], 17.5)
        self.assertTrue(p.array[1] is np.ma.masked)
        self.assertTrue(p.raw_array[1] is np.ma.masked)
        # Get a value not in the mapping
        self.assertEqual(p.array[2], '?')
        self.assertEqual(p.raw_array[2], 9)

    def test_combine_submasks(self):
        p = Parameter('Submasks', submasks={
            'mask1': np.array([1, 0, 0], dtype=np.bool_),
            'mask2': np.array([1, 1, 0], dtype=np.bool_),
        })
        self.assertEqual(p.combine_submasks().tolist(), [1, 1, 0])

    def test_get_array(self):
        array = np.ma.array([10, 20, 30], mask=[0, 1, 1])
        p = Parameter('Submasks', array=array, submasks={
            'mask1': np.array([1, 0, 0], dtype=np.bool_),
            'mask2': np.array([1, 1, 0], dtype=np.bool_),
        })
        self.assertEqual(p.get_array().tolist(), [10, None, None])
        self.assertEqual(p.get_array('mask1').tolist(), [None, 20, 30])
        self.assertEqual(p.get_array('mask2').tolist(), [None, None, 30])

    def test_get_array__mapped(self):
        array = np.ma.array([1, 2, 3], mask=[0, 1, 1])
        values_mapping = {1: 'One', 2: 'Two', 3: 'Three'}
        p = Parameter('Submasks', array=array, submasks={
            'mask1': np.array([1, 0, 0], dtype=np.bool_),
            'mask2': np.array([1, 1, 0], dtype=np.bool_),
        }, values_mapping=values_mapping)
        self.assertEqual(p.get_array().raw.tolist(), [1, None, None])
        self.assertEqual(p.get_array('mask1').raw.tolist(), [None, 2, 3])
        self.assertEqual(p.get_array('mask2').raw.tolist(), [None, None, 3])
        self.assertTrue(isinstance(p.get_array('mask1'), MappedArray))


if __name__ == '__main__':
    unittest.main()

# tests/test_bloom_filter.py

import math
import unittest

from pybloom import BloomFilter  # Import from the new package name


class TestBloomFilter(unittest.TestCase):
    def test_initialization_valid(self):
        """Test successful initialization with valid parameters."""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        self.assertIsInstance(bf, BloomFilter)
        self.assertEqual(bf.expected_items, 1000)
        self.assertEqual(bf.false_positive_rate, 0.01)
        self.assertGreater(bf.num_bits, 0)
        self.assertGreater(bf.num_hashes, 0)
        self.assertEqual(len(bf._bit_array), math.ceil(bf.num_bits / 8))
        self.assertEqual(len(bf), 0)  # Initial item count

    def test_initialization_invalid_params(self):
        """Test initialization with invalid parameters."""
        with self.assertRaises(ValueError):
            BloomFilter(expected_items=0, false_positive_rate=0.1)  # n <= 0
        with self.assertRaises(ValueError):
            BloomFilter(expected_items=-100, false_positive_rate=0.1)
        with self.assertRaises(ValueError):
            BloomFilter(expected_items=100, false_positive_rate=0.0)  # p <= 0
        with self.assertRaises(ValueError):
            BloomFilter(expected_items=100, false_positive_rate=1.0)  # p >= 1
        with self.assertRaises(ValueError):
            BloomFilter(expected_items=100, false_positive_rate=1.5)
        with self.assertRaises(ValueError):
            BloomFilter(expected_items="abc", false_positive_rate=0.1)  # Non-integral n
        with self.assertRaises(ValueError):
            BloomFilter(expected_items=100, false_positive_rate="high")  # Non-real p

    def test_add_and_contains(self):
        """Test adding items and checking containment."""
        bf = BloomFilter(100, 0.05)
        items_to_add = ["apple", "banana", "cherry", 123, 45.6, (1, 2)]
        items_not_added = ["grape", "kiwi", 789, 10.0, (3, 4)]

        for item in items_to_add:
            bf.add(item)

        self.assertEqual(len(bf), len(items_to_add))

        for item in items_to_add:
            self.assertTrue(item in bf, f"Item {item} should be reported as present")
            self.assertTrue(
                bf.might_contain(item), f"Item {item} should be reported as present"
            )

        fp_count = 0
        for item in items_not_added:
            if item in bf:
                fp_count += 1

        print(
            f"\n[test_add_and_contains] False positive count for non-added items: {fp_count}/{len(items_not_added)}"
        )

    def test_add_duplicates(self):
        """Test adding the same item multiple times."""
        bf = BloomFilter(50, 0.1)
        bf.add("hello")
        bf.add("world")
        bf.add("hello")  # Add duplicate

        self.assertEqual(len(bf), 2)  # Length counts add calls, not unique items
        self.assertTrue("hello" in bf)
        self.assertTrue("world" in bf)
        self.assertFalse("goodbye" in bf)  # Assuming no FP for this simple case

    def test_clear(self):
        """Test clearing the filter."""
        bf = BloomFilter(100, 0.01)
        bf.add("test1")
        bf.add("test2")
        self.assertEqual(len(bf), 2)
        self.assertTrue("test1" in bf)

        bf.clear()

        self.assertEqual(len(bf), 0)
        self.assertFalse("test1" in bf)
        self.assertFalse("test2" in bf)
        self.assertEqual(bf._bit_array, bytearray(bf.num_bytes))

    def test_initial_data(self):
        """Test initialization with initial data."""
        initial = {"a", "b", "c"}
        bf = BloomFilter(10, 0.1, initial_data=initial)
        self.assertEqual(len(bf), len(initial))
        self.assertTrue("a" in bf)
        self.assertTrue("b" in bf)
        self.assertTrue("c" in bf)
        self.assertFalse("d" in bf)  # Assuming no FP

    def test_parameter_calculation(self):
        """Test if parameter calculation seems reasonable."""
        bf = BloomFilter(1000, 0.01)
        self.assertAlmostEqual(bf.num_bits, 9585, delta=1)
        self.assertAlmostEqual(bf.num_hashes, 7, delta=1)

        bf = BloomFilter(1000000, 0.0001)
        self.assertAlmostEqual(bf.num_bits, 19170117, delta=1)
        self.assertAlmostEqual(bf.num_hashes, 13, delta=1)

        bf = BloomFilter(1, 0.1)
        self.assertGreaterEqual(bf.num_bits, 1)
        self.assertGreaterEqual(bf.num_hashes, 1)

    def test_hashing_consistency(self):
        """Test that hashing produces consistent indices for the same item."""
        bf = BloomFilter(100, 0.01)
        item = "consistent_test"
        hashes1 = list(bf._get_hashes(item))
        hashes2 = list(bf._get_hashes(item))
        self.assertEqual(hashes1, hashes2)
        self.assertEqual(len(hashes1), bf.num_hashes)
        for h in hashes1:
            self.assertIsInstance(h, int)
            self.assertGreaterEqual(h, 0)
            self.assertLess(h, bf.num_bits)

    def test_current_false_positive_rate(self):
        """Test the current false positive rate estimation."""
        n = 1000
        p = 0.01
        bf = BloomFilter(n, p)

        self.assertAlmostEqual(bf.current_false_positive_rate(), 0.0, delta=1e-9)

        items = [f"item_{i}" for i in range(n)]
        for item in items:
            bf.add(item)

        current_p = bf.current_false_positive_rate()
        print(
            f"\n[test_current_fp_rate] Estimated FP rate after {n} adds: {current_p:.4f} (Target: {p})"
        )
        self.assertLess(current_p, p * 5)
        self.assertGreaterEqual(current_p, 0.0)
        self.assertLessEqual(current_p, 1.0)

        for i in range(n // 2):
            bf.add(f"extra_item_{i}")

        current_p_overloaded = bf.current_false_positive_rate()
        print(
            f"[test_current_fp_rate] Estimated FP rate after {n + n // 2} adds: {current_p_overloaded:.4f}"
        )
        self.assertGreater(current_p_overloaded, current_p)
        self.assertLessEqual(current_p_overloaded, 1.0)

    def test_contains_on_empty_filter(self):
        """Test checking containment on an empty filter."""
        bf = BloomFilter(100, 0.1)
        self.assertFalse("anything" in bf)
        self.assertEqual(len(bf), 0)

    def test_different_item_types(self):
        """Test adding and checking different data types."""
        bf = BloomFilter(50, 0.05)
        items = ["string", 12345, 3.14159, True, None, ("tuple", 1), b"bytes_string"]
        for item in items:
            bf.add(item)

        self.assertEqual(len(bf), len(items))

        for item in items:
            self.assertTrue(
                item in bf, f"Item {item} (type: {type(item)}) should be present"
            )

        self.assertFalse("another_string" in bf)
        self.assertFalse(54321 in bf)
        self.assertFalse(2.718 in bf)
        self.assertFalse(False in bf)
        self.assertFalse(("tuple", 2) in bf)
        self.assertFalse(b"other_bytes" in bf)


if __name__ == "__main__":
    unittest.main()

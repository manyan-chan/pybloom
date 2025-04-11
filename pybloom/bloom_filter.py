# bloom_filter_pkg/bloom_filter.py

import hashlib
import math
import numbers
from typing import Any, Iterable, Optional, Tuple

# A value to slightly alter the seed for the second hash function in double hashing
_HASH_SALT_SUFFIX = b"$_salt_$"


class BloomFilter:
    """
    A space-efficient probabilistic data structure for checking set membership.

    Bloom Filters allow for false positives (might report an item is present
    when it isn't) but guarantee no false negatives (will never report an item
    is absent when it has been added).

    Uses the double hashing technique described by Kirsch & Mitzenmacher (2006)
    to generate multiple hash functions from two base hash functions (SHA256 and
    MD5 in this implementation for simplicity and built-in availability).
    """

    def __init__(
        self,
        expected_items: int,
        false_positive_rate: float,
        initial_data: Optional[Iterable[Any]] = None,
    ):
        """
        Initializes a Bloom Filter.

        Args:
            expected_items (int): The expected number of items to be added (n).
                                  Must be a positive integer.
            false_positive_rate (float): The desired maximum false positive
                                         probability (p) when the filter contains
                                         'expected_items'. Must be > 0.0 and < 1.0.
            initial_data (Optional[Iterable[Any]]): An optional iterable of items
                                                    to add to the filter upon initialization.

        Raises:
            ValueError: If expected_items is not positive or
                        false_positive_rate is not between 0.0 and 1.0.
        """
        if not isinstance(expected_items, numbers.Integral) or expected_items <= 0:
            raise ValueError("expected_items (n) must be a positive integer.")
        if not isinstance(false_positive_rate, numbers.Real) or not (
            0.0 < false_positive_rate < 1.0
        ):
            raise ValueError(
                "false_positive_rate (p) must be between 0.0 and 1.0 (exclusive)."
            )

        self._expected_items = expected_items
        self._fp_rate = false_positive_rate

        # Calculate optimal size (m) and number of hash functions (k)
        self._num_bits, self._num_hashes = self._calculate_optimal_params(
            self._expected_items, self._fp_rate
        )

        # Ensure at least 1 bit and 1 hash function
        self._num_bits = max(1, self._num_bits)
        self._num_hashes = max(1, self._num_hashes)

        # Size of the byte array needed to store _num_bits
        self._num_bytes = math.ceil(self._num_bits / 8)

        # The bit array (using bytearray for mutable sequence of bytes)
        self._bit_array = bytearray(self._num_bytes)

        # Count of items actually added
        self._items_added_count = 0

        # Add initial data if provided
        if initial_data:
            for item in initial_data:
                self.add(item)

    @staticmethod
    def _calculate_optimal_params(n: int, p: float) -> Tuple[int, int]:
        """
        Calculates the optimal bit array size (m) and number of hash functions (k).

        Formulas from Wikipedia / standard Bloom Filter resources:
          m = - (n * ln(p)) / (ln(2)^2)
          k = (m / n) * ln(2)

        Args:
            n: Expected number of items.
            p: Desired false positive rate.

        Returns:
            Tuple[int, int]: (number_of_bits, number_of_hash_functions)
        """
        if n <= 0:  # Should be caught by __init__, but safeguard here
            return 1, 1
        try:
            # Calculate m (number of bits)
            m_float = -(n * math.log(p)) / (math.log(2) ** 2)
            m = int(math.ceil(m_float))

            # Calculate k (number of hash functions)
            k_float = (m / n) * math.log(2)
            k = int(math.ceil(k_float))

        except (ValueError, OverflowError):
            # Handle potential math domain errors or overflow with extreme p values
            # Fallback to minimal safe values
            return 1, 1

        # Ensure m and k are at least 1
        return max(1, m), max(1, k)

    def _get_hashes(self, item: Any) -> Iterable[int]:
        """
        Generates k hash indices for the given item using double hashing.

        Args:
            item: The item to hash.

        Returns:
            An iterable of k integer hash indices (0 <= index < self._num_bits).
        """
        # Convert item to bytes for consistent hashing
        # Using repr() for broader type support, though str() might also work
        try:
            item_bytes = repr(item).encode("utf-8")
        except Exception as e:
            raise TypeError(
                f"Item {item} could not be reliably converted to bytes for hashing: {e}"
            )

        # Generate two base hashes using different algorithms or seeds
        # Using SHA-256 and MD5 for simplicity and built-in availability
        # Note: MD5 is cryptographically weak but fine for non-security hashing distribution
        hash1_bytes = hashlib.sha256(item_bytes).digest()
        hash2_bytes = hashlib.md5(
            item_bytes + _HASH_SALT_SUFFIX
        ).digest()  # Add salt for distinctness

        # Convert hash digests to integers. Use the first 8 bytes (64 bits) for wider range.
        # Using 'big' endianness, but 'little' would also work consistently.
        h1 = int.from_bytes(hash1_bytes[:8], byteorder="big", signed=False)
        h2 = int.from_bytes(hash2_bytes[:8], byteorder="big", signed=False)

        # Generate k indices using the double hashing formula: (h1 + i * h2) % m
        for i in range(self._num_hashes):
            index = (h1 + i * h2) % self._num_bits
            yield index

    def add(self, item: Any) -> None:
        """
        Adds an item to the Bloom Filter.

        Args:
            item: The item to add.
        """
        indices_set = False
        for index in self._get_hashes(item):
            byte_index = index // 8
            bit_offset = index % 8
            # Set the bit using bitwise OR
            mask = 1 << bit_offset
            if not (self._bit_array[byte_index] & mask):
                # Only count as "added" if at least one new bit was set
                # This is an approximation, as multiple adds might flip the same bits
                # A more accurate count tracks unique items added externally if needed
                # For __len__, we simply increment on every call to add()
                indices_set = True  # Track if *any* index was processed
            self._bit_array[byte_index] |= mask

        # Increment count only if we processed indices (i.e., hash generation succeeded)
        if (
            indices_set or self._num_hashes == 0
        ):  # Handle edge case of k=0? (shouldn't happen with checks)
            self._items_added_count += 1

    def might_contain(self, item: Any) -> bool:
        """
        Checks if an item *might* be in the Bloom Filter.

        Args:
            item: The item to check.

        Returns:
            bool: True if the item might be in the set (could be a false positive).
                  False if the item is definitely not in the set.
        """
        if self._num_bits == 0:  # Empty filter case
            return False

        for index in self._get_hashes(item):
            byte_index = index // 8
            bit_offset = index % 8
            # Check if the bit is set using bitwise AND
            mask = 1 << bit_offset
            if not (self._bit_array[byte_index] & mask):
                # If any required bit is 0, the item is definitely not present
                return False

        # If all required bits were 1, the item *might* be present
        return True

    def __contains__(self, item: Any) -> bool:
        """
        Allows using the 'in' operator (e.g., `item in bloom_filter`).
        Equivalent to calling `might_contain(item)`.
        """
        return self.might_contain(item)

    def __len__(self) -> int:
        """
        Returns the number of times `add` has been called.

        Note: This is *not* the number of unique items if duplicates were added,
        nor is it an estimate of the number of unique items based on bit saturation.
        It simply tracks the calls to the `add` method.
        """
        return self._items_added_count

    @property
    def expected_items(self) -> int:
        """Returns the expected number of items (n) the filter was designed for."""
        return self._expected_items

    @property
    def false_positive_rate(self) -> float:
        """Returns the target false positive rate (p) the filter was designed for."""
        return self._fp_rate

    @property
    def num_bits(self) -> int:
        """Returns the size of the bit array (m)."""
        return self._num_bits

    @property
    def num_bytes(self) -> int:
        """Returns the size of the underlying byte array."""
        return self._num_bytes

    @property
    def num_hashes(self) -> int:
        """Returns the number of hash functions used (k)."""
        return self._num_hashes

    def current_false_positive_rate(self) -> float:
        """
        Estimates the current false positive rate based on the number of items added.

        Formula: (1 - exp(-k * n_current / m))^k
        where n_current is the number of items added (`len(self)`).

        Returns:
            float: The estimated current false positive probability. Returns 1.0
                   if calculation is not possible (e.g., m=0).
        """
        n_current = self._items_added_count
        k = self._num_hashes
        m = self._num_bits

        if m == 0:
            return 1.0  # Undefined or completely full

        try:
            exponent = -k * n_current / m
            # Clamp exponent to avoid potential overflow with large negative numbers in exp
            # exp(-710) is roughly 1e-308, close to the limit for float64
            clamped_exponent = max(exponent, -709.0)
            rate = (1 - math.exp(clamped_exponent)) ** k
        except (OverflowError, ValueError):
            # Handle potential math issues, likely indicates saturation
            rate = 1.0
        return rate

    def clear(self) -> None:
        """Resets the Bloom Filter to its initial empty state."""
        self._bit_array = bytearray(self._num_bytes)  # Recreate or fill with zeros
        # Alternatively: self._bit_array[:] = b'\x00' * self._num_bytes
        self._items_added_count = 0

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"expected_items={self._expected_items}, "
            f"false_positive_rate={self._fp_rate}, "
            f"num_bits={self._num_bits}, "
            f"num_hashes={self._num_hashes}, "
            f"items_added={self._items_added_count})"
        )

    # Potential future additions: union, intersection, serialization methods

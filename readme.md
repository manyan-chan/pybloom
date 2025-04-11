# PyBloom

A simple, pure Python implementation of a Bloom Filter named `pybloom`, a space-efficient probabilistic data structure used to test whether an element is a member of a set.

This implementation uses **only built-in Python libraries** (`math`, `hashlib`, `numbers`, `typing`) and is compatible with **Python 3.7+**.

## Key Features

*   **No External Dependencies:** Works out-of-the-box with standard Python.
*   **Python 3.7+ Compatible:** Modern Python syntax and type hints.
*   **Standard Bloom Filter:** Implements core `add` and `might_contain` (`in`) operations.
*   **Optimal Parameter Calculation:** Automatically calculates bit array size (`m`) and hash count (`k`) based on desired capacity (`n`) and false positive rate (`p`).
*   **Double Hashing:** Uses SHA256 and MD5 (with salting) as base hashes to generate `k` hash functions efficiently.
*   **Basic Usage Example Included.**
*   **Unit Tests Included.**
*   **Packaging Files Included (`pyproject.toml`).**
*   **GitHub Actions CI Workflow Included.**

## What is a Bloom Filter?

*   It's like a set, but uses much less memory.
*   You can add items to it.
*   You can ask if an item *might* be in it.
*   **False Positives Possible:** It might say an item is present even if it was never added. The probability of this is configurable.
*   **No False Negatives:** If it says an item is *not* present, it is definitely not present.
*   Items cannot be reliably removed from a standard Bloom Filter.

## Installation

You can install this package directly from the source directory using pip:

```bash
# Clone the repository (if you haven't already)
# git clone https://github.com/manyan-chan/pybloom.git
# cd pybloom

# Install in editable mode (good for development)
pip install -e .

# Or install normally
pip install .
```

*(If this were published to PyPI, you could install via `pip install pybloom`)*

## Basic Usage

```python
# Import the BloomFilter class from the pybloom package
# *** UPDATED IMPORT ***
from pybloom import BloomFilter

# Initialize with expected capacity and desired false positive rate
bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

print(f"Filter created: m={bf.num_bits} bits, k={bf.num_hashes} hashes")

# Add items
bf.add("apple")
bf.add(123)
bf.add(("a", "tuple"))

print(f"Items added: {len(bf)}") # Note: len() counts 'add' calls

# Check for membership (uses 'in' operator)
print(f"'apple' in filter? {'apple' in bf}")  # Output: True
print(f"'banana' in filter? {'banana' in bf}") # Output: False (likely)
print(f"123 in filter? {123 in bf}")         # Output: True
print(f"456 in filter? {456 in bf}")         # Output: False (likely)

# Check the estimated current false positive rate
print(f"Estimated current FP rate: {bf.current_false_positive_rate():.4f}")

# Clear the filter
bf.clear()
print(f"'apple' in filter after clear? {'apple' in bf}") # Output: False
```

See the `examples/basic_usage.py` file for a more detailed example.

## Running Tests

Unit tests are included in the `tests/` directory and use Python's built-in `unittest` module.

To run the tests from the root `pybloom/` directory:

```bash
python -m unittest discover tests
```

## API

*   `BloomFilter(expected_items: int, false_positive_rate: float, initial_data: Optional[Iterable] = None)`: Constructor.
*   `add(item: Any)`: Adds an item to the filter.
*   `might_contain(item: Any) -> bool`: Checks if item might be present.
*   `__contains__(item: Any) -> bool`: Allows `item in filter` syntax (calls `might_contain`).
*   `__len__() -> int`: Returns the number of times `add` was called.
*   `clear()`: Resets the filter.
*   `current_false_positive_rate() -> float`: Estimates the current FP rate based on items added.
*   Properties: `expected_items`, `false_positive_rate`, `num_bits`, `num_bytes`, `num_hashes`.

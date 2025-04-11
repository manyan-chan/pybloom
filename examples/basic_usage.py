# examples/basic_usage.py

# Import the BloomFilter class
import random
import string

from pybloom import BloomFilter

# 1. Initialize the Bloom Filter
num_items_expected = 10000
fp_rate_target = 0.01
print(
    f"Initializing Bloom Filter for {num_items_expected} items with target FP rate {fp_rate_target}"
)
bf = BloomFilter(expected_items=num_items_expected, false_positive_rate=fp_rate_target)
print(f" -> Calculated bit array size (m): {bf.num_bits}")
print(f" -> Calculated number of hash functions (k): {bf.num_hashes}")
print(f" -> Initial length (items added): {len(bf)}")
print("-" * 20)

# 2. Add some items
items_to_add = ["apple", "banana", "orange", "grape", "lemon", "lime", 123, True]
print(f"Adding {len(items_to_add)} items: {items_to_add}")
for item in items_to_add:
    bf.add(item)
print(f" -> Current length (items added): {len(bf)}")
print("-" * 20)

# 3. Check for items known to be added
print("Checking for items that were added:")
for item in items_to_add:
    print(f"  '{item}' in filter? {item in bf}")
print("-" * 20)

# 4. Check for items known *not* to be added
items_not_added = ["strawberry", "kiwi", "pineapple", 456, False, "grapefruit"]
print("Checking for items that were NOT added:")
false_positives = 0
for item in items_not_added:
    result = item in bf
    print(f"  '{item}' in filter? {result}", end="")
    if result:
        print(" <-- Potential False Positive!")
        false_positives += 1
    else:
        print("")
print(
    f"\n -> Found {false_positives} potential false positives out of {len(items_not_added)} checks."
)
print(f" -> Estimated current FP rate: {bf.current_false_positive_rate():.5f}")
print("-" * 20)

# 5. Add more items
num_to_add_more = num_items_expected - len(bf)
print(f"Adding {num_to_add_more} more random items...")

for i in range(num_to_add_more):
    random_item = "".join(random.choices(string.ascii_lowercase, k=10)) + str(i)
    bf.add(random_item)
print(f" -> Current length (items added): {len(bf)}")
print(
    f" -> Estimated FP rate near capacity: {bf.current_false_positive_rate():.5f} (Target was {fp_rate_target})"
)
print("-" * 20)

# 6. Check again for non-added items
print("Re-checking for items that were NOT added (after more adds):")
false_positives = 0
for item in items_not_added:
    result = item in bf
    print(f"  '{item}' in filter? {result}", end="")
    if result:
        print(" <-- Potential False Positive!")
        false_positives += 1
    else:
        print("")
print(
    f"\n -> Found {false_positives} potential false positives out of {len(items_not_added)} checks."
)
print("-" * 20)

# 7. Clear the filter
print("Clearing the filter...")
bf.clear()
print(f" -> Length after clear: {len(bf)}")
print(f" -> 'apple' in filter after clear? {'apple' in bf}")
print(f" -> Estimated FP rate after clear: {bf.current_false_positive_rate():.5f}")

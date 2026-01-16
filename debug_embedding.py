import os
import sys
import importlib

# Clear any cached modules to ensure fresh imports
modules_to_clear = [k for k in sys.modules.keys() if k.startswith('src')]
for module in modules_to_clear:
    del sys.modules[module]

# Set environment variables
os.environ['QDRANT_URL'] = 'http://localhost:6333'
os.environ['OPENROUTER_API_KEY'] = 'test-key'

print("Testing the exact functions that are used in the failing request...")

# Import and test the retrieving function that's called during retrieval
from src.services.retrieving import get_embedding
test_text = "Hello world"
embedding = get_embedding(test_text)
print(f"get_embedding() produces vector of length: {len(embedding)}")
print(f"First few values: {embedding[:5]}")

# Test the retrieve function that's called during the API request
from src.services.retrieving import retrieve
try:
    # This will fail due to Qdrant connection, but we want to see if embedding dimension is the issue
    results = retrieve("test query", limit=1)
    print(f"retrieve() successful: {len(results)} results")
except Exception as e:
    error_msg = str(e)
    print(f"retrieve() failed: {error_msg}")
    if "dimension" in error_msg.lower() or "dim:" in error_msg:
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print("FOUND THE DIMENSION ERROR! The issue is in the retrieve() function")
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

print("\\nTesting completed. If dimension error occurred above, that's where the issue is.")
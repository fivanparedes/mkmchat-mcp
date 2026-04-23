
import sys
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.append(os.getcwd())

from mkmchat.data.rag import RAGSystem

rag = RAGSystem()
rag.index_data()

print(f"Total documents: {len(rag.documents)}")
found = False
for doc in rag.documents:
    if "Horde Chef" in doc.content:
        print(f"Found: {doc.metadata.get('name')} | Content preview: {doc.content[:100]}...")
        found = True

if not found:
    print("Horde Chef not found in indexed documents!")

"""Test memory integration."""

import os
import json
from src.memory.manager import MemoryManager
from src.models import AtomicNote, ClaimReview
from datetime import datetime

def test_memory_manager():
    print("=== Testing Memory Manager ===")
    
    # Clear existing memory
    if os.path.exists("memory_store.json"):
        os.remove("memory_store.json")
    
    memory = MemoryManager()
    
    # Test adding a note
    note = AtomicNote(
        content="The sky is blue.",
        tags=["nature", "color"],
        confidence=0.9,
        timestamp=datetime.now().isoformat()
    )
    memory.add_note(note)
    print("✓ Added note")
    
    # Test searching notes
    results = memory.search_notes("sky")
    assert len(results) == 1
    assert results[0].content == "The sky is blue."
    print("✓ Searched notes")
    
    # Test saving a review
    review = ClaimReview(
        claim_reviewed="Is the sky blue?",
        review_rating="TRUE",
        rating_score=5,
        review_body="Yes, it is.",
        author="TestAgent",
        date_published=datetime.now().isoformat()
    )
    memory.save_claim_review(review)
    print("✓ Saved review")
    
    # Test retrieving a review
    retrieved = memory.get_claim_review("Is the sky blue?")
    assert retrieved is not None
    assert retrieved.review_rating == "TRUE"
    print("✓ Retrieved review")
    
    print("Memory Manager Tests Passed!")

if __name__ == "__main__":
    test_memory_manager()

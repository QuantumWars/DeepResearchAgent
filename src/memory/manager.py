"""Memory Manager for the fact-checking system."""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.models import AtomicNote, ClaimReview

MEMORY_FILE = "memory_store.json"

class MemoryManager:
    """Manages storage and retrieval of Atomic Notes and Claim Reviews."""

    def __init__(self, memory_file: str = MEMORY_FILE):
        self.memory_file = memory_file
        self.notes: List[Dict[str, Any]] = []
        self.reviews: List[Dict[str, Any]] = []
        self._load_memory()

    def _load_memory(self):
        """Load memory from JSON file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.notes = data.get("notes", [])
                    self.reviews = data.get("reviews", [])
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {self.memory_file}. Starting with empty memory.")
                self.notes = []
                self.reviews = []
        else:
            self.notes = []
            self.reviews = []

    def _save_memory(self):
        """Save memory to JSON file."""
        data = {
            "notes": self.notes,
            "reviews": self.reviews
        }
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_note(self, note: AtomicNote):
        """Add an Atomic Note to memory."""
        # Simple deduplication check based on content
        for existing in self.notes:
            if existing["content"] == note.content:
                # Update metadata or confidence if needed? For now, just skip.
                return
        
        self.notes.append(note.model_dump())
        self._save_memory()

    def search_notes(self, query: str, limit: int = 5) -> List[AtomicNote]:
        """Search for relevant notes (simple keyword matching for now)."""
        query_lower = query.lower()
        results = []
        
        for note_data in self.notes:
            note_content = note_data.get("content", "").lower()
            tags = [t.lower() for t in note_data.get("tags", [])]
            
            score = 0
            if query_lower in note_content:
                score += 2
            for tag in tags:
                if tag in query_lower:
                    score += 1
            
            if score > 0:
                results.append((score, note_data))
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        return [AtomicNote(**r[1]) for r in results[:limit]]

    def save_claim_review(self, review: ClaimReview):
        """Save a finalized ClaimReview."""
        # Remove existing review for same claim if exists
        self.reviews = [r for r in self.reviews if r["claim_reviewed"] != review.claim_reviewed]
        self.reviews.append(review.model_dump())
        self._save_memory()

    def get_claim_review(self, claim: str) -> Optional[ClaimReview]:
        """Retrieve an existing ClaimReview for a claim."""
        # Exact match for now, could be fuzzy later
        for review_data in self.reviews:
            if review_data["claim_reviewed"].lower() == claim.lower():
                return ClaimReview(**review_data)
        return None

    def get_all_reviews(self) -> List[ClaimReview]:
        return [ClaimReview(**r) for r in self.reviews]

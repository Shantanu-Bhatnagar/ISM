"""
Enterprise Data Deduplication & Compression Engine
Features: Fixed-block & Content-addressable hashing (SHA-256), Block Reference Counting,
Storage savings analytics, Recipe Reassembly, and Garbage Collection.
"""

import hashlib
import zlib
from typing import Dict, List, Any, Optional

class DeduplicationBlock:
    def __init__(self, block_hash: str, raw_data: bytes, block_id: int):
        self.block_hash = block_hash
        self.block_id = block_id
        self.ref_count = 1
        self.size_bytes = len(raw_data)
        # Store compressed data to demonstrate inline compression
        self.compressed_data = zlib.compress(raw_data)
        self.compressed_size = len(self.compressed_data)
        self.sample_preview = raw_data[:16].decode('utf-8', errors='replace')

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "block_hash": self.block_hash[:12] + "...",
            "full_hash": self.block_hash,
            "ref_count": self.ref_count,
            "size_bytes": self.size_bytes,
            "compressed_size": self.compressed_size,
            "sample_preview": self.sample_preview
        }


class DeduplicationEngine:
    def __init__(self, chunk_size: int = 16):
        self.chunk_size = chunk_size
        # Hash -> DeduplicationBlock
        self.block_index: Dict[str, DeduplicationBlock] = {}
        # filename -> list of block_hashes (file recipe)
        self.file_recipes: Dict[str, List[str]] = {}
        self.next_block_id = 1
        self.total_raw_ingested_bytes = 0

    def ingest_data(self, filename: str, content: str) -> Dict[str, Any]:
        """Ingests a file or string, chunks it, detects duplicate blocks, and stores unique ones."""
        data_bytes = content.encode('utf-8')
        self.total_raw_ingested_bytes += len(data_bytes)
        
        # Fixed-size chunking
        chunks = [data_bytes[i:i + self.chunk_size] for i in range(0, len(data_bytes), self.chunk_size)]
        if not chunks:
            chunks = [b'']

        file_recipe: List[str] = []
        unique_added = 0
        duplicate_detected = 0

        for chunk in chunks:
            h = hashlib.sha256(chunk).hexdigest()
            file_recipe.append(h)
            
            if h in self.block_index:
                # Duplicate block found! Increment reference pointer
                self.block_index[h].ref_count += 1
                duplicate_detected += 1
            else:
                # Unique block - allocate new physical block
                block = DeduplicationBlock(block_hash=h, raw_data=chunk, block_id=self.next_block_id)
                self.block_index[h] = block
                self.next_block_id += 1
                unique_added += 1

        self.file_recipes[filename] = file_recipe

        stats = self.get_stats()
        return {
            "status": "SUCCESS",
            "filename": filename,
            "chunks_total": len(chunks),
            "unique_blocks_stored": unique_added,
            "duplicate_blocks_referenced": duplicate_detected,
            "dedup_ratio": stats["deduplication_ratio"],
            "space_saved_percent": stats["space_saved_percent"],
            "recipe_hashes": [h[:10] for h in file_recipe]
        }

    def delete_file(self, filename: str) -> Dict[str, Any]:
        """Decrements reference counters. If ref_count drops to 0, frees physical space (Garbage Collection)."""
        if filename not in self.file_recipes:
            return {"status": "ERROR", "message": f"File '{filename}' not found"}

        recipe = self.file_recipes.pop(filename)
        freed_blocks = 0
        for h in recipe:
            if h in self.block_index:
                self.block_index[h].ref_count -= 1
                if self.block_index[h].ref_count <= 0:
                    del self.block_index[h]
                    freed_blocks += 1

        return {
            "status": "SUCCESS",
            "message": f"File {filename} deleted. Garbage collection reclaimed {freed_blocks} orphaned blocks.",
            "freed_blocks": freed_blocks,
            "stats": self.get_stats()
        }

    def get_stats(self) -> Dict[str, Any]:
        total_unique_blocks = len(self.block_index)
        total_physical_raw_bytes = sum(b.size_bytes for b in self.block_index.values())
        total_physical_compressed_bytes = sum(b.compressed_size for b in self.block_index.values())
        
        # Calculate virtual bytes (what all files would take without deduplication)
        virtual_raw_bytes = sum(
            sum(self.block_index[h].size_bytes for h in hashes if h in self.block_index)
            for hashes in self.file_recipes.values()
        )
        if virtual_raw_bytes == 0:
            virtual_raw_bytes = self.total_raw_ingested_bytes

        if total_physical_raw_bytes > 0:
            dedup_ratio = round(virtual_raw_bytes / total_physical_raw_bytes, 2)
            space_saved_bytes = max(0, virtual_raw_bytes - total_physical_raw_bytes)
            space_saved_percent = round((space_saved_bytes / virtual_raw_bytes) * 100, 1) if virtual_raw_bytes > 0 else 0.0
        else:
            dedup_ratio = 1.0
            space_saved_bytes = 0
            space_saved_percent = 0.0

        return {
            "total_files": len(self.file_recipes),
            "total_unique_blocks": total_unique_blocks,
            "virtual_raw_bytes": virtual_raw_bytes,
            "physical_raw_bytes": total_physical_raw_bytes,
            "physical_compressed_bytes": total_physical_compressed_bytes,
            "space_saved_bytes": space_saved_bytes,
            "space_saved_percent": space_saved_percent,
            "deduplication_ratio": f"{dedup_ratio}:1",
            "files_list": list(self.file_recipes.keys()),
            "blocks_preview": [b.to_dict() for b in list(self.block_index.values())[-10:]]
        }

    def clear(self):
        self.block_index.clear()
        self.file_recipes.clear()
        self.next_block_id = 1
        self.total_raw_ingested_bytes = 0

"""
VoiceForge — Qdrant Initialization Script
==========================================
Run this once before starting the server to create collections and seed templates.

Usage:
    python scripts/init_qdrant.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.qdrant_service import QdrantService


async def main():
    print("🔧 Initializing VoiceForge Qdrant collections...")
    
    qdrant = QdrantService()
    
    print("  Creating collections...")
    await qdrant.initialize_collections()
    
    print("  Seeding document templates...")
    await qdrant.seed_templates()
    
    print("✅ Qdrant initialization complete!")
    print("\nCollections created:")
    print("  • user_preferences  — stores accessibility settings per user")
    print("  • document_templates — pre-built form/doc templates")
    print("  • session_memory    — conversation history and context")
    print("  • generated_docs    — records of all created documents")


if __name__ == "__main__":
    asyncio.run(main())

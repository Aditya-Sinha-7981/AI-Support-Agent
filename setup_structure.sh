#!/bin/bash
# Run this once after cloning to create all empty __init__.py files
# and placeholder directories that git won't track otherwise
# Usage: bash setup_structure.sh

echo "Creating folder structure..."

# Backend package init files
touch backend/providers/__init__.py
touch backend/providers/llm/__init__.py
touch backend/providers/stt/__init__.py
touch backend/providers/tts/__init__.py
touch backend/rag/__init__.py
touch backend/agent/__init__.py
touch backend/api/__init__.py

# Data directories (git won't track empty folders)
mkdir -p backend/data/documents/banking
mkdir -p backend/data/documents/ecommerce
mkdir -p backend/data/indexes/banking
mkdir -p backend/data/indexes/ecommerce

# Keep files so git tracks the empty dirs
touch backend/data/documents/banking/.gitkeep
touch backend/data/documents/ecommerce/.gitkeep
touch backend/data/indexes/banking/.gitkeep
touch backend/data/indexes/ecommerce/.gitkeep

# Logs folder for local md files (gitignored)
mkdir -p logs
touch logs/m1.local.md
touch logs/m2.local.md
touch logs/m3.local.md
touch logs/m4.local.md

# From repo root
mkdir -p backend/rag
mkdir -p backend/api
mkdir -p backend/agent
mkdir -p docs

# Move backend files
mv pipeline.py backend/rag/pipeline.py
mv chat.py backend/api/chat.py
mv voice.py backend/api/voice.py
mv memory.py backend/agent/memory.py
mv main.py backend/main.py
mv config.py backend/config.py
mv requirements.txt backend/requirements.txt
mv .env.example backend/.env.example

# Move docs
mv API_CONTRACT.md docs/API_CONTRACT.md

# These stay at root
# mock_server.py ← root is correct
# setup_structure.sh ← root is correct
# README.md ← root is correct
# .gitignore ← root is correct

echo "Done. Run the following next:"
echo ""
echo "  cd backend"
echo "  python -m venv venv"
echo "  source venv/bin/activate   # Mac/Linux"
echo "  venv\Scripts\activate      # Windows"
echo "  pip install -r requirements.txt"
echo "  cp .env.example .env"
echo "  # Fill in your API keys in .env"

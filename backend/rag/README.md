# RAG System - Phase 1 Implementation Complete

## Overview
Implemented a Retrieval-Augmented Generation (RAG) system to improve agent reliability by retrieving relevant example workflows based on semantic similarity.

## Architecture

```
backend/rag/
├── __init__.py                  # Module exports
├── .gitignore                   # Ignore embeddings.json
├── retriever.py                 # Runtime retrieval logic
├── build_embeddings.py          # Offline embedding generation
├── embeddings.json              # Generated (gitignored)
└── examples/
    ├── coffee_shop.md           # Coffee shop promo example
    └── perfume_promo.md         # Perfume promo example

backend/services/google/
└── GeminiEmbeddingProvider.py   # text-embedding-004 wrapper

backend/business_logic/
└── invoke_agent.py              # Integrated RAG retrieval
```

## Components

### 1. Examples (Markdown Format)
- **Location**: `backend/rag/examples/*.md`
- **Format**: Pure conversational markdown (no frontmatter metadata)
- **Current Examples**:
  - `coffee_shop.md` - 15s promotional video workflow
  - `perfume_promo.md` - Product promo with image-to-video

### 2. Embedding Provider
- **File**: `backend/services/google/GeminiEmbeddingProvider.py`
- **Model**: `text-embedding-004`
- **Methods**:
  - `embed_single(text)` - For runtime queries
  - `embed_batch(texts)` - For corpus building

### 3. Build Script
- **File**: `backend/rag/build_embeddings.py`
- **Function**: Generates embeddings for all examples
- **Output**: `embeddings.json` with structure:
  ```json
  [
    {
      "filename": "coffee_shop.md",
      "content": "# Coffee Shop...",
      "embedding": [0.123, ...],
      "embedding_dim": 768
    }
  ]
  ```

### 4. Retriever
- **File**: `backend/rag/retriever.py`
- **Key Functions**:
  - `load_embeddings()` - Load and cache embeddings
  - `retrieve_examples(query, k=1)` - Find top-K similar examples
  - `cosine_similarity()` - Compare vectors
- **Algorithm**: Numpy cosine similarity (brute force, fast for small corpus)

### 5. Integration
- **File**: `backend/business_logic/invoke_agent.py`
- **Flow**:
  1. Extract latest user message
  2. Call `retrieve_examples(user_message, k=1)`
  3. Append retrieved example to system prompt
  4. Continue with normal agent flow
- **Fallback**: Gracefully continues without example if retrieval fails

## Usage

### First Time Setup
```bash
cd backend
python -m rag.build_embeddings
```

This generates `embeddings.json` from all `.md` files in `examples/`.

### Adding New Examples
1. Create new `.md` file in `backend/rag/examples/`
2. Write pure conversational content (no metadata needed)
3. Regenerate embeddings:
   ```bash
   python -m rag.build_embeddings
   ```

### How It Works at Runtime
1. User sends message: "Create a coffee shop video"
2. RAG retrieves most similar example: `coffee_shop.md` (similarity=0.92)
3. Example appended to system prompt
4. Agent responds with workflow similar to retrieved example
5. Quality and consistency improve significantly

## Key Design Decisions

✅ **Markdown files** - Easy to read, edit, and version control  
✅ **No metadata** - Embeddings capture semantic meaning naturally  
✅ **Gitignored embeddings** - Can regenerate anytime from examples  
✅ **Simple retrieval** - Numpy cosine similarity, no vector DB needed  
✅ **Graceful fallback** - System continues if RAG fails  
✅ **Latest message only** - Retrieves based on most recent user input  

## Next Steps (Phase 2)

1. **Generate embeddings**: Run `build_embeddings.py` for first time
2. **Test retrieval**: Verify correct examples retrieved for different queries
3. **Monitor quality**: Track which examples are retrieved and agent success rates
4. **Expand corpus**: Add more examples (product demos, explainers, tutorials)
5. **Tune retrieval**: Adjust k value, similarity thresholds, or query preprocessing
6. **Add metrics**: Log retrieval scores and downstream success

## Testing Plan

Test these queries to verify retrieval:
- "Create a coffee shop promo" → should retrieve `coffee_shop.md`
- "Make a video from my perfume image" → should retrieve `perfume_promo.md`
- "Generate a product video" → should retrieve based on similarity
- Generic queries → verify graceful fallback

## Dependencies

- `google-genai` - Gemini API client (already installed)
- `numpy` - Vector math for cosine similarity (needs to be added to pyproject.toml)

## Notes

- Embeddings are cached in memory after first load for performance
- Each retrieval requires one embedding API call for the query
- Build script requires one embedding API call per example
- All examples embedded offline, no runtime overhead except query embedding

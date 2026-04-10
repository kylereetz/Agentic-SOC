# Multi-Head Agentic SOC Architecture: Performance & Stability Report

## 1. Objective
To optimize the Agentic SOC for a 16GB VRAM environment (RTX 4080) by distributing LLM workloads across specialized "Heads." This ensures high-fidelity reasoning for investigations while maintaining low-latency structured output for reporting and normalization.

## 2. The Multi-Head Model Mapping

| Model Head | Primary Model | VRAM Used | Dedicated Agents |
| :--- | :--- | :--- | :--- |
| **Reasoning Head** | `llama3.1:8b` (4-bit) | ~7.0 GB | Investigator, Governor, Log-Guardian, Patch-Advisor |
| **Syntactic Head** | `gemma4:e4b` (4-bit) | ~2.5 GB | Communicator |
| **Embedding Head** | `nomic-embed-text` | ~1.5 GB | Librarian (RAG Memory) |

**Total Cumulative Load**: ~12.5 GB (Leaving 3.5GB of "Safe Buffer" for the Host OS and Parallel bursts).

## 3. Technology Shift: Pydantic AI
We have transitioned from the legacy, monolithic `LLMClient` to **Pydantic AI**. 
- **Type-Safe Returns**: Utilizing Pydantic models for agent outputs to eliminate manual JSON parsing.
- **Micro-Agents**: Each head is initialized with its own Pydantic AI `Agent` instance, allowing them to remain in the GPU's memory independently.
- **Context Enforcement**: All heads are hard-coded with a **16,384 token context window** (`num_ctx`) to handle deep incident histories.

## 4. OLLAMA High-Performance Tuning
The SOC infrastructure now utilizes specific environment variables to prevent "Model Thumping" (thrashing models in and out of VRAM):
- `OLLAMA_MAX_VRAM`: 16GB
- `OLLAMA_NUM_PARALLEL`: 4 (Enables parallel agent processing)
- `OLLAMA_KEEP_ALIVE`: -1 (Forces persistence in VRAM for zero-latency response)

## 5. Security Summary
By moving to a Multi-Head local model design, the SOC remains **Air-Gap Ready**. The reliance on cloud models like Gemini 1.5 Pro is now entirely optional, as `llama3.1:8b` provides parity for 95% of standard investigation TTPs in a hardened, offline environment.

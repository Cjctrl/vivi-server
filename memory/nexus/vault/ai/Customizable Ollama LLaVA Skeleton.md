---
tags: [user, customizable_ollama_llava_skeleton, claude, ai-conversation]
---



# Customizable Ollama LLaVA Skeleton

**Created:** 2025-06-02 14:41  
**Updated:** 2025-06-02 14:43

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2025-06-02 14:41

make me a ollama with llava skeleton so I can easily change it... add to this prompt and enachced

---

### 🤖 Claude · 2025-06-02 14:43

I'll create a flexible Ollama with LLaVA skeleton that you can easily customize. This will include a clean structure with enhanced features for image analysis.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

I've created an enhanced Ollama LLaVA skeleton with the following features:

## **Key Features:**
- **Flexible Configuration**: Easily change models, hosts, temperature, and context size
- **Multiple Prompt Types**: Pre-built prompts for detailed, concise, technical, creative, and accessible analysis
- **Three Operation Modes**: Single image, batch processing, and interactive mode
- **Error Handling**: Robust error handling with detailed feedback
- **CLI Interface**: Command-line arguments for easy automation
- **JSON Output**: Structured results with metadata and timestamps
- **Progress Tracking**: Real-time feedback for batch operations

## **Usage Examples:**

```bash
# Interactive mode (recommended for exploration)
python llava_client.py --interactive

# Single image analysis
python llava_client.py --image "photo.jpg" --prompt-type "detailed"

# Batch processing
python llava_client.py --batch *.jpg --output "results.json"

# Custom prompt
python llava_client.py --image "photo.jpg" --custom-prompt "What safety issues do you see?"

# Different model
python llava_client.py --model "llava:13b" --image "photo.jpg"
```

## **Easy Customization:**
1. **Add new prompt types** in the `system_prompts` dictionary
2. **Modify default parameters** in the `__init__` method
3. **Add custom processing** in the `analyze_image` method
4. **Extend output formats** by modifying the return dictionaries

## **Prerequisites:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull LLaVA model
ollama pull llava:latest

# Install Python dependencies
pip install ollama
```

The skeleton is designed to be production-ready while remaining easy to modify for your specific use cases. Would you like me to add any specific features or modify any part of the implementation?

---
claude-conversations-hub customizable-ollama-llava-skeleton

## Tags
#claude-conversations-hub #customizable #customizable-ollama-llava-skeleton

import sys
import os

# Add current directory to path so PyCatan can be imported
sys.path.append(os.getcwd())

try:
    from PyCatan.Agents.llm_engine import OllamaProvider
    
    provider = OllamaProvider(base_url="http://127.0.0.1:11434", model="qwen2.5:0.5b")
    
    try:
        # Attempt to generate with a timeout
        response = provider.generate("Test prompt", timeout=15)
        print("success")
        transport = response.get('transport', 'api')
        print(f"transport: {transport}")
        text = response.get('text', '')
        print(text[:120])
    except Exception as e:
        print("failure")
        print(f"{type(e).__name__}: {str(e)}")

except Exception as e:
    print(f"Import/Setup Error: {type(e).__name__}: {str(e)}")

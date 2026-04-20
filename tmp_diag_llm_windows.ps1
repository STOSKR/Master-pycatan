Set-Location 'A:\Master-pycatan'
$env:PYTHONPATH = 'A:\Master-pycatan;A:\Master-pycatan\PyCatan'
$env:CATAN_LLM_PROVIDER = 'ollama'
$env:CATAN_LLM_MODEL = 'qwen2.5:0.5b'
$env:CATAN_OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
python A:\Master-pycatan\tmp_diag_llm_windows.py

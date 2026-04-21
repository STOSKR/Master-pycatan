Set-Location 'A:\Master-pycatan'

$env:PYTHONPATH = 'A:\Master-pycatan;A:\Master-pycatan\PyCatan'
$env:CATAN_LLM_PROVIDER = 'ollama'
$env:CATAN_LLM_MODEL = 'qwen2.5:0.5b'
$env:CATAN_OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
$env:CATAN_BENCH_N_MATCHES = '2'
$env:CATAN_BENCH_MAX_ROUNDS = '25'

$ollamaPath = 'C:\Users\Shiyi Cheng yi\AppData\Local\Programs\Ollama\ollama.exe'
if (Test-Path $ollamaPath) {
  Start-Process -FilePath $ollamaPath -ArgumentList 'serve' -WindowStyle Hidden
}

Write-Host '=== RANDOM START ==='
$start = Get-Date
python A:\Master-pycatan\PyCatan\benchmark_vs_random.py
$duration = (Get-Date) - $start
Write-Host ("=== RANDOM END ({0:n3}s) ===" -f $duration.TotalSeconds)

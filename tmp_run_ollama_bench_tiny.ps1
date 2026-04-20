Set-Location 'A:\Master-pycatan'
$env:PYTHONPATH = 'A:\Master-pycatan;A:\Master-pycatan\PyCatan'
$env:CATAN_LLM_PROVIDER = 'ollama'
$env:CATAN_LLM_MODEL = 'qwen2.5:0.5b'
$env:CATAN_OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
$env:CATAN_BENCH_N_MATCHES_PER_PERM = '1'
$env:CATAN_BENCH_MAX_PERMUTATIONS = '1'
$env:CATAN_BENCH_N_MATCHES = '2'
$env:CATAN_BENCH_MAX_ROUNDS = '25'

Write-Host '=== STANDARD START ==='
$start1 = Get-Date
python A:\Master-pycatan\PyCatan\benchmark_vs_agentes_estandar.py
$dur1 = (Get-Date) - $start1
Write-Host ("=== STANDARD END ({0:n3}s) ===" -f $dur1.TotalSeconds)

Write-Host '=== RANDOM START ==='
$start2 = Get-Date
python A:\Master-pycatan\PyCatan\benchmark_vs_random.py
$dur2 = (Get-Date) - $start2
Write-Host ("=== RANDOM END ({0:n3}s) ===" -f $dur2.TotalSeconds)

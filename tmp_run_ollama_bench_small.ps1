Set-Location 'A:\Master-pycatan'
$env:PYTHONPATH='A:\Master-pycatan;A:\Master-pycatan\PyCatan'
$env:CATAN_LLM_PROVIDER='ollama'
$env:CATAN_LLM_MODEL='qwen2.5:0.5b'
$env:CATAN_OLLAMA_BASE_URL='http://127.0.0.1:11434'
$env:CATAN_BENCH_N_MATCHES_PER_PERM='1'
$env:CATAN_BENCH_MAX_PERMUTATIONS='8'
$env:CATAN_BENCH_N_MATCHES='12'
Write-Host 'Starting benchmark_vs_agentes_estandar.py...'
$start1 = Get-Date
python A:\Master-pycatan\PyCatanenchmark_vs_agentes_estandar.py
$end1 = Get-Date
$duration1 = $end1 - $start1
Write-Host 'Duration for benchmark_vs_agentes_estandar.py: ' $duration1

Write-Host 'Starting benchmark_vs_random.py...'
$start2 = Get-Date
python A:\Master-pycatan\PyCatanenchmark_vs_random.py
$end2 = Get-Date
$duration2 = $end2 - $start2
Write-Host 'Duration for benchmark_vs_random.py: ' $duration2

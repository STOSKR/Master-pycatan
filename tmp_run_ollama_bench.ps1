Set-Location 'A:\Master-pycatan'
$env:PYTHONPATH = 'A:\Master-pycatan;A:\Master-pycatan\PyCatan'
$env:CATAN_LLM_PROVIDER = 'ollama'
$env:CATAN_LLM_MODEL = 'qwen2.5:0.5b'
$env:CATAN_OLLAMA_BASE_URL = 'http://127.0.0.1:11434'

Write-Host "--- START BENCHMARK VS AGENTES ESTANDAR ---"
$startTime = Get-Date
python A:\Master-pycatan\PyCatan\benchmark_vs_agentes_estandar.py
$endTime = Get-Date
$duration = $endTime - $startTime
Write-Host "--- END BENCHMARK VS AGENTES ESTANDAR ---"
Write-Host "Runtime: $($duration.TotalSeconds) seconds"

Write-Host "--- START BENCHMARK VS RANDOM ---"
$startTime = Get-Date
python A:\Master-pycatan\PyCatan\benchmark_vs_random.py
$endTime = Get-Date
$duration = $endTime - $startTime
Write-Host "--- END BENCHMARK VS RANDOM ---"
Write-Host "Runtime: $($duration.TotalSeconds) seconds"

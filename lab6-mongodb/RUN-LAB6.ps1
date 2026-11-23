$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force -Path .\outputs | Out-Null
$jobs = @(
  @('lab6_1_index_workload','Activity_6.1_Index_Workload\lab6_1_index_workload.py'),
  @('lab6_1_try_index_stats','Activity_6.1_Try_IndexStats\lab6_1_try_index_stats.py'),
  @('lab6_2_index_strategies','Activity_6.2_Index_Strategies\lab6_2_index_strategies.py'),
  @('lab6_2_try_covered_query','Activity_6.2_Try_Covered_Query\lab6_2_try_covered_query.py')
)
foreach ($item in $jobs) {
  $name=$item[0]; $job=$item[1]
  Write-Host "`n=========== $name ===========" -ForegroundColor Cyan
  & python $job 2>&1 | Tee-Object -FilePath "outputs/$name.txt"
  if ($LASTEXITCODE -ne 0) { throw "Activity failed: $name (exit code $LASTEXITCODE)" }
}
Write-Host "`nAll 4 Lab 6 activities passed. Save screenshots from the REAL terminal." -ForegroundColor Green

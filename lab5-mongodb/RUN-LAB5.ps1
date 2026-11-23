# Run from the Lab 5 root folder; no existing project data is deleted.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$jobs = @(
  'Activity_5.1_Sales_Analytics/lab5_1_sales_analytics.py',
  'Activity_5.1_Try_Bucket/lab5_1_try_bucket.py',
  'Activity_5.2_Lookup_Joins/lab5_2_lookup_joins.py',
  'Activity_5.2_Try_Lookup_Pipeline/lab5_2_try_lookup_pipeline.py'
)
New-Item -ItemType Directory -Force -Path outputs | Out-Null
foreach($job in $jobs) {
  $name = [IO.Path]::GetFileNameWithoutExtension($job)
  Write-Host "`n========== $name ==========" -ForegroundColor Cyan
  python $job 2>&1 | Tee-Object -FilePath "outputs/$name.txt"
  if ($LASTEXITCODE -ne 0) { throw "Activity failed: $name" }
}
Write-Host "`nAll 4 Lab 5 activities passed. Save real terminal screenshots for submission." -ForegroundColor Green

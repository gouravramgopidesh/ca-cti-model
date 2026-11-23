# Run in PowerShell from this folder after installing requirements.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$jobs = @(
  "Activity_4.1_Product_Query_API/lab4_1_product_queries.py",
  "Activity_4.1_Try_Regex_Search/lab4_1_try_regex.py",
  "Activity_4.2_Upsert_Bulk/lab4_2_upsert_bulk.py",
  "Activity_4.2_Try_Idempotent_Import/lab4_2_try_import.py"
)
New-Item -ItemType Directory -Force -Path "outputs" | Out-Null
foreach ($job in $jobs) {
  $name = [System.IO.Path]::GetFileNameWithoutExtension($job)
  Write-Host "`n========== $name ==========" -ForegroundColor Cyan
  # Tee-Object preserves console output and writes text evidence. Screenshots must be captured on your own PC.
  python $job 2>&1 | Tee-Object -FilePath "outputs/$name.txt"
  if ($LASTEXITCODE -ne 0) { throw "Activity failed: $name" }
}
Write-Host "`nAll 4 activities passed. Capture screenshots of your real terminal for submission." -ForegroundColor Green

$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -like '*main.py*' -or $_.CommandLine -like '*KS SnapClip*') }
if ($procs) {
    $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Output "Stopped $($_.ProcessId)" }
} else {
    Write-Output 'No matching KS SnapClip processes found'
}
$ErrorActionPreference = "Stop"
try {
    $excel = New-Object -ComObject Excel.Application
    $filePath = Join-Path (Get-Location) "target_report.xlsx"
    $wb = $excel.Workbooks.Open($filePath, $false, $true)
    
    # First list all sheet names with index so we can target correctly
    $i = 1
    foreach ($sheet in $wb.Sheets) {
        Write-Host "$i : $($sheet.Name)"
        $i++
    }
    
    $wb.Close($false)
    $excel.Quit()
} catch {
    Write-Error $_.Exception.Message
} finally {
    if ($excel) { [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null }
}

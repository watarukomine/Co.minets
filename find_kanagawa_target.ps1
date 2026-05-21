$ErrorActionPreference = "Stop"
try {
    $excel = New-Object -ComObject Excel.Application
    $filePath = Join-Path (Get-Location) "target_report.xlsx"
    $wb = $excel.Workbooks.Open($filePath, $false, $true)
    
    foreach ($sheet in $wb.Sheets) {
        Write-Host "SCANNING Sheet: $($sheet.Name)"
        $res = $sheet.UsedRange.Find("85371")
        if ($res) {
            Write-Host "FOUND 85371 in $($sheet.Name) at Row $($res.Row)"
            $line = ""
            for ($c = 1; $c -le 15; $c++) {
                $line += "$($sheet.Cells.Item($res.Row, $c).Text) | "
            }
            Write-Host "DATA: $line"
        }
    }
    $wb.Close($false)
    $excel.Quit()
} catch {
    Write-Error $_.Exception.Message
} finally {
    if ($excel) { [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null }
}

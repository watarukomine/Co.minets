$ErrorActionPreference = "Stop"
try {
    $excel = New-Object -ComObject Excel.Application
    $filePath = Join-Path (Get-Location) "target_report.xlsx"
    $wb = $excel.Workbooks.Open($filePath, $false, $true)
    
    # Dump sheets 7, 8, 9, 10 (0-indexed would be 8,9,10,11 in 1-based)
    $targetIndices = @(7, 8, 9, 10)
    $output = @()
    
    foreach ($idx in $targetIndices) {
        $sheet = $wb.Sheets.Item($idx)
        $output += "=== SHEET $idx : $($sheet.Name) ==="
        $lastRow = [Math]::Min($sheet.UsedRange.Rows.Count, 60)
        $lastCol = [Math]::Min($sheet.UsedRange.Columns.Count, 25)
        for ($r = 1; $r -le $lastRow; $r++) {
            $line = "R$($r): "
            for ($c = 1; $c -le $lastCol; $c++) {
                $val = $sheet.Cells.Item($r, $c).Text
                $line += "[$val]"
            }
            $output += $line
        }
        $output += ""
    }
    
    $output | Out-File "sheets_7_8_9_10_dump.txt" -Encoding utf8
    $wb.Close($false)
    $excel.Quit()
} catch {
    Write-Error $_.Exception.Message
} finally {
    if ($excel) { [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null }
}

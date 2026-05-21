$ErrorActionPreference = "Stop"
try {
    $excel = New-Object -ComObject Excel.Application
    # Use relative path or join with current directory
    $filePath = Join-Path (Get-Location) "【A3印刷用】0417_改良2026年3月度実績集.xlsx"
    $wb = $excel.Workbooks.Open($filePath, $false, $true)
    
    foreach ($sheet in $wb.Sheets) {
        # Just print ALL sheet names first to be sure
        Write-Host "Sheet: $($sheet.Name)"
        
        # If the user says it's only Kanagawa, maybe the first sheet IS Kanagawa data and I misread it?
        # Let's search for "神奈川" or "371" anywhere in the sheet
        $res = $sheet.UsedRange.Find("85371")
        if ($res) {
            Write-Host "FOUND 85371 in $($sheet.Name) at Row $($res.Row)"
            $line = ""
            for ($c = 1; $c -le 15; $c++) {
                $line += "$($sheet.Cells.Item($res.Row, $c).Text) | "
            }
            Write-Host $line
        }
    }
    $wb.Close($false)
    $excel.Quit()
} catch {
    Write-Error $_.Exception.Message
} finally {
    if ($excel) { [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null }
}

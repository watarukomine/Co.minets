$ErrorActionPreference = "Stop"
try {
    $excel = New-Object -ComObject Excel.Application
    $wb = $excel.Workbooks.Open("x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx", $false, $true) # Open Read-only
    
    foreach ($sheet in $wb.Sheets) {
        if ($sheet.Name -like "*神奈川*" -or $sheet.Name -like "*371*") {
            Write-Host "FOUND Target Sheet: $($sheet.Name)"
            $lastRow = $sheet.UsedRange.Rows.Count
            for ($r = 1; $r -le [Math]::Min($lastRow, 100); $r++) {
                $line = ""
                for ($c = 1; $c -le 15; $c++) {
                    $line += "$($sheet.Cells.Item($r, $c).Text) | "
                }
                Write-Host $line
            }
        }
    }
    $wb.Close($false)
    $excel.Quit()
} catch {
    Write-Error $_.Exception.Message
} finally {
    if ($excel) { [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null }
}

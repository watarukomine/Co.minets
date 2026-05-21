$ErrorActionPreference = "Stop"
try {
    $excel = New-Object -ComObject Excel.Application
    $filePath = Join-Path (Get-Location) "target_report.xlsx"
    $wb = $excel.Workbooks.Open($filePath, $false, $true)
    $sheet = $wb.Sheets.Item(1)
    
    $output = @()
    for ($r = 1; $r -le 100; $r++) {
        $line = ""
        for ($c = 1; $c -le 20; $c++) {
            $val = $sheet.Cells.Item($r, $c).Text
            $line += "[$val] "
        }
        $output += $line
    }
    $output | Out-File "table_dump.txt" -Encoding utf8
    $wb.Close($false)
    $excel.Quit()
} catch {
    Write-Error $_.Exception.Message
} finally {
    if ($excel) { [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null }
}

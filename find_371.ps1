$ErrorActionPreference = "Stop"
try {
    $excel = New-Object -ComObject Excel.Application
    $filePath = Join-Path (Get-Location) "target_report.xlsx"
    $wb = $excel.Workbooks.Open($filePath, $false, $true)
    
    foreach ($sheet in $wb.Sheets) {
        # Search for "371" or "神奈川"
        $res = $sheet.UsedRange.Find("371")
        if ($res) {
            Write-Host "FOUND '371' in $($sheet.Name) at Row $($res.Row) Col $($res.Column)"
            Write-Host "DATA: $($sheet.Cells.Item($res.Row, $res.Column).Text)"
            # Print the whole row
            $line = ""
            for ($c = 1; $c -le 15; $c++) { $line += "$($sheet.Cells.Item($res.Row, $c).Text) | " }
            Write-Host "ROW DATA: $line"
        }
        
        $res2 = $sheet.UsedRange.Find("神奈川")
        if ($res2) {
            Write-Host "FOUND '神奈川' in $($sheet.Name) at Row $($res2.Row) Col $($res2.Column)"
            Write-Host "DATA: $($sheet.Cells.Item($res2.Row, $res2.Column).Text)"
        }
    }
    $wb.Close($false)
    $excel.Quit()
} catch {
    Write-Host "Error: $($_.Exception.Message)"
} finally {
    if ($excel) { [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null }
}

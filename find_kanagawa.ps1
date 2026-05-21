$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open("x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx")

$target = "85371"
$found = $false

foreach ($sheet in $wb.Sheets) {
    $res = $sheet.UsedRange.Find($target)
    if ($res) {
        Write-Host "FOUND Kanagawa in Sheet: $($sheet.Name) at Row: $($res.Row)"
        $row = $res.Row
        $data = @()
        for ($c = 1; $c -le 15; $c++) {
            $data += $sheet.Cells.Item($row, $c).Text
        }
        Write-Host "DATA: $($data -join ' | ')"
        $found = $true
        break
    }
}

$wb.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

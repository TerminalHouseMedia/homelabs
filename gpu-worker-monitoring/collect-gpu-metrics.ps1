param([string]$MetricsDirectory = 'C:\ProgramData\THM\metrics')
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$directory = $MetricsDirectory
New-Item -ItemType Directory -Path $directory -Force | Out-Null
$destination = Join-Path $directory 'nvidia.prom'
$temporary = Join-Path $directory 'nvidia.prom.tmp'
$lines = [System.Collections.Generic.List[string]]::new()
$inv = [Globalization.CultureInfo]::InvariantCulture
$now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
try {
 $smi = (Get-Command nvidia-smi.exe -ErrorAction Stop).Source
 $rows = & $smi --query-gpu=index,name,temperature.gpu,power.draw,power.limit,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits
 if ($LASTEXITCODE -ne 0) { throw 'GPU query failed' }
 $metrics = @(@('thm_gpu_temperature_celsius',2,1),@('thm_gpu_power_watts',3,1),@('thm_gpu_power_limit_watts',4,1),@('thm_gpu_memory_used_bytes',5,1048576),@('thm_gpu_memory_total_bytes',6,1048576),@('thm_gpu_utilization_percent',7,1))
 foreach ($row in $rows) {
  $fields = @($row.Split(',') | ForEach-Object {$_.Trim()})
  if ($fields.Count -lt 8) { throw 'Unexpected GPU query columns' }
  $gpu = $fields[0]
  foreach ($metric in $metrics) {
   $value = 0.0
   if ([double]::TryParse($fields[$metric[1]], [Globalization.NumberStyles]::Float, $inv, [ref]$value)) {
    $lines.Add($metric[0] + '{gpu="' + $gpu + '"} ' + ($value * $metric[2]).ToString('R',$inv))
   }
  }
 }
 $lines.Add('thm_gpu_collect_success 1')
} catch {
 $lines.Clear()
 $lines.Add('thm_gpu_collect_success 0')
}
$lines.Add('thm_gpu_collect_timestamp_seconds ' + $now)
$lines.Add('thm_host_memory_total_bytes ' + ([int64](Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory).ToString($inv))
[IO.File]::WriteAllText($temporary, ($lines -join "`n") + "`n", [Text.UTF8Encoding]::new($false))
Move-Item $temporary $destination -Force

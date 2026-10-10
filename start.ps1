param(
    [switch]$Test,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'
$pythonExe = Join-Path $backendDir '.venv\Scripts\python.exe'
$runDir = Join-Path $projectRoot '.run'
$startedProcesses = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()
$startedOllama = $false
$scriptFailed = $false

function Write-Step([string]$message) {
    Write-Host "`n[Local Transcript AI] $message" -ForegroundColor Cyan
}

function Wait-Http([string]$url, [string]$name, [int]$timeoutSeconds = 45) {
    $deadline = (Get-Date).AddSeconds($timeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "  OK: $name" -ForegroundColor Green
                return
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    } while ((Get-Date) -lt $deadline)
    throw "$name не запустился за $timeoutSeconds секунд. Проверьте логи в $runDir"
}

function Start-HiddenProcess(
    [string]$filePath,
    [string[]]$arguments,
    [string]$workingDirectory,
    [string]$logName
) {
    $stdout = Join-Path $runDir "$logName.out.log"
    $stderr = Join-Path $runDir "$logName.err.log"
    $process = Start-Process -FilePath $filePath -ArgumentList $arguments `
        -WorkingDirectory $workingDirectory -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $startedProcesses.Add($process)
    return $process
}

function Stop-ProcessTree([int]$rootProcessId) {
    $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $rootProcessId" -ErrorAction SilentlyContinue)
    foreach ($child in $children) {
        Stop-ProcessTree ([int]$child.ProcessId)
    }
    if (Get-Process -Id $rootProcessId -ErrorAction SilentlyContinue) {
        Stop-Process -Id $rootProcessId -Force -ErrorAction SilentlyContinue
        try {
            Wait-Process -Id $rootProcessId -Timeout 5 -ErrorAction SilentlyContinue
        } catch {}
    }
}

try {
    Write-Step 'Проверка окружения'
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        throw "Python-окружение не найдено: $pythonExe`nВыполните инструкции установки backend из README.md."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $frontendDir 'node_modules'))) {
        throw "Frontend-зависимости не установлены. Выполните: cd frontend; npm install"
    }
    $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npmCommand) { throw 'npm не найден в PATH.' }
    $ollamaCommand = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if (-not $ollamaCommand) { $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue }
    if (-not $ollamaCommand) { throw 'Ollama не найдена в PATH. Установите Ollama и перезапустите PowerShell.' }

    New-Item -ItemType Directory -Force -Path $runDir | Out-Null

    $cudaRoot = $env:CUDA_PATH
    if (-not $cudaRoot -or -not (Test-Path (Join-Path $cudaRoot 'bin\cublas64_12.dll'))) {
        $cudaRoot = Get-ChildItem 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA' -Directory -ErrorAction SilentlyContinue |
            Where-Object { Test-Path (Join-Path $_.FullName 'bin\cublas64_12.dll') } |
            Sort-Object Name -Descending |
            Select-Object -First 1 -ExpandProperty FullName
    }
    if ($cudaRoot) {
        $cudaBin = Join-Path $cudaRoot 'bin'
        $env:PATH = "$cudaBin;$env:PATH"
        Write-Host "  CUDA runtime: $cudaRoot" -ForegroundColor DarkGray
    }
    Write-Step 'Запуск Ollama'
    try {
        Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2 | Out-Null
        Write-Host '  OK: Ollama уже запущена' -ForegroundColor Green
    } catch {
        $ollamaProcess = Start-HiddenProcess $ollamaCommand.Source @('serve') $projectRoot 'ollama'
        $startedOllama = $true
        Wait-Http 'http://127.0.0.1:11434/api/tags' 'Ollama' 30
    }

    Write-Step 'Запуск FastAPI backend'
    $backendProcess = Start-HiddenProcess $pythonExe @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000') $backendDir 'backend'
    Wait-Http 'http://127.0.0.1:8000/api/health' 'Backend' 45

    Write-Step 'Запуск Vite frontend'
    $frontendProcess = Start-HiddenProcess $npmCommand.Source @('run','dev','--','--host','127.0.0.1','--strictPort') $frontendDir 'frontend'
    Wait-Http 'http://127.0.0.1:5173' 'Frontend' 45

    Write-Host "`nПроект запущен: http://127.0.0.1:5173" -ForegroundColor Green
    Write-Host "API:             http://127.0.0.1:8000/docs"
    Write-Host "Логи:            $runDir"

    if (-not $NoBrowser -and -not $Test) {
        Start-Process 'http://127.0.0.1:5173'
    }

    if ($Test) {
        Write-Host "`nТест запуска успешно пройден." -ForegroundColor Green
    } else {
        Write-Host "`nОставьте это окно открытым. Для остановки нажмите Ctrl+C." -ForegroundColor Yellow
        while ($true) {
            foreach ($process in $startedProcesses) {
                if ($process.HasExited) {
                    throw "Процесс $($process.Id) неожиданно завершился. Проверьте логи в $runDir"
                }
            }
            Start-Sleep -Seconds 2
        }
    }
} catch {
    $scriptFailed = $true
    Write-Host "`nОшибка запуска: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    if ($Test) {
        Write-Step 'Остановка тестовых процессов'
    } else {
        Write-Host "`nОстанавливаю Local Transcript AI..." -ForegroundColor Yellow
    }
    foreach ($process in $startedProcesses) {
        if ($process) {
            Stop-ProcessTree ([int]$process.Id)
        }
    }
    if (-not $startedOllama) {
        Write-Host '  Существующий процесс Ollama оставлен запущенным.' -ForegroundColor DarkGray
    }
}

if ($scriptFailed) { exit 1 }

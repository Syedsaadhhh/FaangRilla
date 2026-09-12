# OpenDoor Relay - Run 1 Verification Script (PowerShell)
# Strict automated verification of the hero recovery loop. Exits nonzero on failure.

$ErrorActionPreference = 'Stop'
$BaseUrl = 'http://127.0.0.1:8000'

Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host ' OpenDoor Relay - Run 1 Automated Hero Path Verification ' -ForegroundColor Cyan
Write-Host '==========================================================' -ForegroundColor Cyan

$spawnedProcess = $null

# 1. Check if backend is running, or start it temporarily
$healthCheck = $null
try {
    $healthCheck = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
} catch {
    $healthCheck = $null
}

if (-not $healthCheck) {
    Write-Host '[1/8] Starting local backend server on port 8000...' -ForegroundColor Yellow
    $pythonExe = "$PSScriptRoot\..\backend\.venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        Write-Error "Python executable not found at $pythonExe."
        exit 1
    }
    
    $spawnedProcess = Start-Process -FilePath $pythonExe -ArgumentList '-m', 'uvicorn', 'opendoor_relay.api.app:app', '--host', '127.0.0.1', '--port', '8000' -PassThru -NoNewWindow
    
    # Wait for backend to be ready
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $h = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($h -and $h.status -eq 'healthy') {
                $ready = $true
                break
            }
        } catch {}
    }
    
    if (-not $ready) {
        Write-Error 'Failed to start backend server within 15 seconds.'
        if ($spawnedProcess) { Stop-Process -Id $spawnedProcess.Id -Force }
        exit 1
    }
}

try {
    # Step 1: Health Check
    Write-Host '[1/9] Verifying GET /health...' -ForegroundColor Green
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    if ($health.status -ne 'healthy') {
        throw "Health check failed: expected 'healthy', got '$($health.status)'"
    }

    # Step 2: Reset to known state & inspect initial state
    Write-Host '[2/9] Resetting synthetic demo data and inspecting initial state...' -ForegroundColor Green
    $null = Invoke-RestMethod -Uri "$BaseUrl/api/demo/reset" -Method Post
    $demo = Invoke-RestMethod -Uri "$BaseUrl/api/demo/event" -Method Get
    
    if ($demo.plan.assigned_provider_id -ne 'prov-a-starlight') {
        throw "Initial assigned provider must be 'prov-a-starlight'"
    }
    if ($demo.case.state -ne 'CONFIRMED') {
        throw "Initial case state must be 'CONFIRMED', got '$($demo.case.state)'"
    }

    # Step 3: Trigger Provider A decline
    Write-Host '[3/9] Triggering Provider A failure (declines 45m before cutoff)...' -ForegroundColor Green
    $body = @{ trigger_text = 'Provider A declared sudden unavailability 45m before readiness cutoff' } | ConvertTo-Json
    $failure = Invoke-RestMethod -Uri "$BaseUrl/api/cases/case-synthetic-001/provider-failure" -Method Post -Body $body -ContentType 'application/json'
    
    if ($failure.case.state -ne 'REPLACEMENT_PENDING') {
        throw "Expected state 'REPLACEMENT_PENDING', got '$($failure.case.state)'"
    }
    if ($failure.offer.provider_id -ne 'prov-b-beacon') {
        throw "Expected eligible backup provider 'prov-b-beacon', got '$($failure.offer.provider_id)'"
    }

    # Extract token from response_url
    $responseUrl = $failure.response_url
    $token = $responseUrl.Substring($responseUrl.LastIndexOf('/') + 1)
    if ([string]::IsNullOrWhiteSpace($token)) {
        throw "Failed to extract provider response token from URL: $responseUrl"
    }

    # Step 4: Validate Provider portal offer retrieval
    Write-Host '[4/9] Validating provider offer details via token...' -ForegroundColor Green
    $offerDetail = Invoke-RestMethod -Uri "$BaseUrl/api/provider/offer/$token" -Method Get
    if ($offerDetail.provider_name -notlike '*Beacon Live Access*') {
        throw 'Provider offer name mismatch: expected Beacon Live Access'
    }

    # Step 5: Provider B accepts offer
    Write-Host '[5/9] Recording Provider B acceptance via single-use token...' -ForegroundColor Green
    $respondBody = @{ action = 'ACCEPT'; response_text = 'Accepted assignment. In transit with CART equipment.' } | ConvertTo-Json
    $respond = Invoke-RestMethod -Uri "$BaseUrl/api/provider/respond/$token" -Method Post -Body $respondBody -ContentType 'application/json'
    
    if ($respond.offer_state -ne 'ACCEPTED') {
        throw "Expected offer state 'ACCEPTED', got '$($respond.offer_state)'"
    }
    if ($respond.case_state -ne 'ATTENDEE_CONFIRMATION_PENDING') {
        throw "Expected case state 'ATTENDEE_CONFIRMATION_PENDING', got '$($respond.case_state)'"
    }

    # Step 6: Verify Idempotency on repeated acceptance
    Write-Host '[6/9] Testing duplicate response idempotency (must produce 0 side-effects)...' -ForegroundColor Green
    $caseBeforeReplay = Invoke-RestMethod -Uri "$BaseUrl/api/cases/case-synthetic-001" -Method Get
    $timelineBefore = Invoke-RestMethod -Uri "$BaseUrl/api/cases/case-synthetic-001/timeline" -Method Get
    
    $null = Invoke-RestMethod -Uri "$BaseUrl/api/provider/respond/$token" -Method Post -Body $respondBody -ContentType 'application/json'
    
    $caseAfterReplay = Invoke-RestMethod -Uri "$BaseUrl/api/cases/case-synthetic-001" -Method Get
    $timelineAfter = Invoke-RestMethod -Uri "$BaseUrl/api/cases/case-synthetic-001/timeline" -Method Get
    
    if ($caseBeforeReplay.plan.version -ne $caseAfterReplay.plan.version) {
        throw "Idempotency violation: Plan version changed on replay from $($caseBeforeReplay.plan.version) to $($caseAfterReplay.plan.version)"
    }
    if ($timelineBefore.audit_events.Count -ne $timelineAfter.audit_events.Count) {
        throw 'Idempotency violation: Duplicate audit event created on replay'
    }

    # Step 7: Attendee confirms replacement
    Write-Host '[7/9] Recording attendee confirmation and locking recovery clock...' -ForegroundColor Green
    $confirm = Invoke-RestMethod -Uri "$BaseUrl/api/cases/case-synthetic-001/attendee-confirm" -Method Post
    if ($confirm.state -ne 'ATTENDEE_CONFIRMED') {
        throw "Expected final state 'ATTENDEE_CONFIRMED', got '$($confirm.state)'"
    }
    if ($null -eq $confirm.time_to_recovered_seconds -or $confirm.time_to_recovered_seconds -lt 0) {
        throw "Invalid measured time_to_recovered_seconds: $($confirm.time_to_recovered_seconds)"
    }
    if ($null -eq $confirm.time_to_confirmed_seconds -or $confirm.time_to_confirmed_seconds -lt 0) {
        throw "Invalid measured time_to_confirmed_seconds: $($confirm.time_to_confirmed_seconds)"
    }

    # Step 8: Verify full chronological timeline and headline recovery metric
    Write-Host '[8/9] Verifying full audit timeline and headline metrics...' -ForegroundColor Green
    $finalTimeline = Invoke-RestMethod -Uri "$BaseUrl/api/cases/case-synthetic-001/timeline" -Method Get
    if ($finalTimeline.audit_events.Count -lt 5) {
        throw "Expected at least 5 audit events, found $($finalTimeline.audit_events.Count)"
    }
    if ($null -eq $finalTimeline.time_to_confirmed_seconds) {
        throw "Headline metric 'time_to_confirmed_seconds' missing from timeline"
    }

    # Step 9: Verify evaluation endpoint explicitly reports NOT_GENERATED for Run 1
    Write-Host '[9/9] Verifying GET /api/evaluation/latest returns explicit NOT_GENERATED state...' -ForegroundColor Green
    $evalStatus = Invoke-RestMethod -Uri "$BaseUrl/api/evaluation/latest" -Method Get
    if ($evalStatus.status -ne 'NOT_GENERATED') {
        throw "Expected evaluation status 'NOT_GENERATED', got '$($evalStatus.status)'"
    }
    if ($evalStatus.run -ne 'RUN_1') {
        throw "Expected run 'RUN_1', got '$($evalStatus.run)'"
    }
    if ($null -ne $evalStatus.results) {
        throw "Results must be null/empty during Run 1"
    }

    Write-Host ''
    Write-Host '==========================================================' -ForegroundColor Green
    Write-Host ' VERIFICATION SUCCESS: Run 1 Local Hero Path PASSED!     ' -ForegroundColor Green
    Write-Host " Headline Metric (Time to Confirmed): $($confirm.time_to_confirmed_seconds) seconds" -ForegroundColor Green
    Write-Host " Supporting Metric (Time to Recovered): $($confirm.time_to_recovered_seconds) seconds" -ForegroundColor Green
    Write-Host " Audit Events Recorded: $($finalTimeline.audit_events.Count)" -ForegroundColor Green
    Write-Host " Evaluation State: $($evalStatus.status) (scheduled for Run 2)" -ForegroundColor Green
    Write-Host '==========================================================' -ForegroundColor Green
    exit 0

} catch {
    Write-Host ''
    Write-Host "VERIFICATION FAILED: $_" -ForegroundColor Red
    exit 1
} finally {
    if ($spawnedProcess) {
        Write-Host 'Cleaning up background backend process...' -ForegroundColor Gray
        Stop-Process -Id $spawnedProcess.Id -Force -ErrorAction SilentlyContinue
    }
}

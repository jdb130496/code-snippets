# chat.ps1 — First message with files

# ── Edit these lines only ──────────────────
$IMAGE    = "C:\Users\YourName\Pictures\screenshot.png"
$PDF      = "C:\Users\YourName\Documents\report.pdf"
$QUESTION = "Analyse both files"
$API_KEY  = "YOUR_API_KEY"
# ──────────────────────────────────────────

# Pricing
$INPUT_PRICE  = 3.00 / 1000000
$OUTPUT_PRICE = 15.00 / 1000000

# Balance file
$BALANCE_FILE = "D:\ClaudeCode\session_balance.txt"
$RUNNING_TOTAL = if (Test-Path $BALANCE_FILE) {
    [decimal](Get-Content $BALANCE_FILE)
} else { 0 }

# Convert files to base64
$IMAGE_B64 = [Convert]::ToBase64String(
    [IO.File]::ReadAllBytes($IMAGE))
$PDF_B64   = [Convert]::ToBase64String(
    [IO.File]::ReadAllBytes($PDF))

# Build JSON body
$BODY = @"
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 16000,
  "thinking": {"type": "adaptive"},
  "output_config": {"effort": "low"},
  "cache_control": {"type": "ephemeral"},
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "$IMAGE_B64"
          }
        },
        {
          "type": "document",
          "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": "$PDF_B64"
          }
        },
        {
          "type": "text",
          "text": "$QUESTION"
        }
      ]
    }
  ]
}
"@

# Send request
$RESPONSE = Invoke-RestMethod `
  -Uri "https://api.anthropic.com/v1/messages" `
  -Method POST `
  -Headers @{
    "x-api-key"         = $API_KEY
    "anthropic-version" = "2023-06-01"
    "content-type"      = "application/json"
  } `
  -Body $BODY

# Extract token usage
$INPUT_TOKENS        = $RESPONSE.usage.input_tokens
$OUTPUT_TOKENS       = $RESPONSE.usage.output_tokens
$CACHE_READ_TOKENS   = $RESPONSE.usage.cache_read_input_tokens
$CACHE_CREATE_TOKENS = $RESPONSE.usage.cache_creation_input_tokens

# Calculate cost
$INPUT_COST    = $INPUT_TOKENS * $INPUT_PRICE
$OUTPUT_COST   = $OUTPUT_TOKENS * $OUTPUT_PRICE
$TOTAL_COST    = $INPUT_COST + $OUTPUT_COST
$RUNNING_TOTAL += $TOTAL_COST

# Save running total
Set-Content $BALANCE_FILE $RUNNING_TOTAL

# Display
Write-Host ""
Write-Host "── RESPONSE ──────────────────────────────"
Write-Host $RESPONSE.content[0].text
Write-Host ""
Write-Host "── TOKEN USAGE ───────────────────────────"
Write-Host "Input tokens:        $INPUT_TOKENS"
Write-Host "Output tokens:       $OUTPUT_TOKENS"
Write-Host "Cache read tokens:   $CACHE_READ_TOKENS"
Write-Host "Cache created:       $CACHE_CREATE_TOKENS"
Write-Host ""
Write-Host "── COST THIS MESSAGE ─────────────────────"
Write-Host ("Input cost:   `${0:F6}" -f $INPUT_COST)
Write-Host ("Output cost:  `${0:F6}" -f $OUTPUT_COST)
Write-Host ("Total:        `${0:F6}" -f $TOTAL_COST)
Write-Host ("In INR:       ₹{0:F4}" -f ($TOTAL_COST * 95))
Write-Host ""
Write-Host "── SESSION RUNNING TOTAL ─────────────────"
Write-Host ("Session total: `${0:F6}" -f $RUNNING_TOTAL)
Write-Host ("Session INR:   ₹{0:F4}" -f ($RUNNING_TOTAL * 95))
Write-Host "──────────────────────────────────────────"

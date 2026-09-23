# followup.ps1

$QUESTION = "Your question here"
$API_KEY  = "YOUR_API_KEY"

# Pricing per token
$INPUT_PRICE  = 3.00 / 1000000   # $3 per million
$OUTPUT_PRICE = 15.00 / 1000000  # $15 per million

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
      "content": "$QUESTION"
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
$INPUT_COST  = $INPUT_TOKENS * $INPUT_PRICE
$OUTPUT_COST = $OUTPUT_TOKENS * $OUTPUT_PRICE
$TOTAL_COST  = $INPUT_COST + $OUTPUT_COST

# Display response
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
Write-Host "──────────────────────────────────────────"

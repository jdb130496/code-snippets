package main

import (
    "bufio"
    "fmt"
    "log"
    "os"
    "strings"

    kiteconnect "github.com/zerodha/gokiteconnect/v4"
)

func loadCredentials(path string) (apiKey, apiSecret, requestToken string) {
    f, err := os.Open(path)
    if err != nil {
        log.Fatal("Cannot open credentials file:", err)
    }
    defer f.Close()

    var lines []string
    scanner := bufio.NewScanner(f)
    for scanner.Scan() {
        line := strings.TrimSpace(scanner.Text())
        if line != "" {
            lines = append(lines, line)
        }
    }
    if len(lines) < 3 {
        log.Fatal("credentials file must have 3 lines: api_key, api_secret, request_token")
    }
    return lines[0], lines[1], lines[2]
}

func main() {
    apiKey, apiSecret, requestToken := loadCredentials(`D:\dev\zerodha-token.txt`)

    // 1. Create client
    kc := kiteconnect.New(apiKey)

    // 2. Exchange request token for access token (run once per session)
    session, err := kc.GenerateSession(requestToken, apiSecret)
    if err != nil {
        log.Fatal("Session error:", err)
    }
    kc.SetAccessToken(session.AccessToken)
    fmt.Println("✓ Login successful")
    fmt.Println("  Access token:", session.AccessToken)

    // 3. Fetch user profile
    profile, err := kc.GetUserProfile()
    if err != nil {
        log.Fatal("Profile error:", err)
    }
    fmt.Println("  User:", profile.UserName, "|", profile.Email)

    // 4. Fetch holdings
    holdings, err := kc.GetHoldings()
    if err != nil {
        log.Fatal("Holdings error:", err)
    }
    fmt.Println("\nHoldings:")
    for _, h := range holdings {
        fmt.Printf("  %-20s qty:%-6d avg:%-10.2f ltp:%-10.2f pnl:%.2f\n",
            h.Tradingsymbol, h.Quantity, h.AveragePrice, h.LastPrice, h.PnL)
    }

    // 5. Fetch positions
    positions, err := kc.GetPositions()
    if err != nil {
        log.Fatal("Positions error:", err)
    }
    fmt.Println("\nDay Positions:")
    for _, p := range positions.Day {
        fmt.Printf("  %-20s qty:%-6d pnl:%.2f\n",
            p.Tradingsymbol, p.Quantity, p.PnL)
    }
}

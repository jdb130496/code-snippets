package main

import (
	"archive/zip"
	"bytes"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/cookiejar"
	"os"
	"path/filepath"
	"time"
)

const outputDir = `D:\bhavcopy_data`

func downloadBhavcopy(dateStr string) (string, error) {
	// Parse DD-MM-YYYY
	date, err := time.Parse("02-01-2006", dateStr)
	if err != nil {
		return "", fmt.Errorf("invalid date format, use DD-MM-YYYY: %w", err)
	}
	dateFormatted := date.Format("20060102")

	archiveURL := fmt.Sprintf(
		"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_%s_F_0000.csv.zip",
		dateFormatted,
	)

	fmt.Printf("Downloading bhavcopy for %s...\n", dateStr)
	fmt.Printf("URL: %s\n", archiveURL)

	// Cookie jar — holds session cookies across requests (same as cffi Session)
	jar, _ := cookiejar.New(nil)
	client := &http.Client{
		Jar:     jar,
		Timeout: 60 * time.Second,
	}

	// Chrome-like headers
	chromeHeaders := map[string]string{
		"User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
		"Accept-Language": "en-US,en;q=0.9",
		"Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
	}

	// Step 1: Warm up on NSE homepage
	fmt.Println("Warming up session on NSE homepage...")
	req, _ := http.NewRequest("GET", "https://www.nseindia.com", nil)
	for k, v := range chromeHeaders {
		req.Header.Set(k, v)
	}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("homepage warmup failed: %w", err)
	}
	resp.Body.Close()

	// Step 2: Build Akamai session tokens
	fmt.Println("Building session cookies...")
	req, _ = http.NewRequest("GET", "https://www.nseindia.com/market-data/live-equity-market", nil)
	for k, v := range chromeHeaders {
		req.Header.Set(k, v)
	}
	resp, err = client.Do(req)
	if err != nil {
		return "", fmt.Errorf("market data page failed: %w", err)
	}
	resp.Body.Close()

	// Step 3: Download the archive
	fmt.Println("Fetching bhavcopy archive...")
	req, _ = http.NewRequest("GET", archiveURL, nil)
	for k, v := range chromeHeaders {
		req.Header.Set(k, v)
	}
	req.Header.Set("Referer", "https://www.nseindia.com/")
	req.Header.Set("Accept", "application/zip, application/octet-stream, */*")

	resp, err = client.Do(req)
	if err != nil {
		return "", fmt.Errorf("archive download failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == 404 {
		fmt.Printf("404 — No bhavcopy for %s (holiday or weekend).\n", dateStr)
		return "", nil
	}
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("unexpected HTTP %d", resp.StatusCode)
	}

	// Save ZIP
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", fmt.Errorf("cannot create output dir: %w", err)
	}
	filename := fmt.Sprintf("BhavCopy_NSE_CM_0_0_0_%s_F_0000.csv.zip", dateFormatted)
	zipPath := filepath.Join(outputDir, filename)

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("reading response: %w", err)
	}
	if err := os.WriteFile(zipPath, body, 0644); err != nil {
		return "", fmt.Errorf("writing zip: %w", err)
	}
	fmt.Printf("Downloaded: %s\n", zipPath)
	return zipPath, nil
}

func extractZip(zipPath string) error {
	fmt.Printf("\nExtracting %s...\n", zipPath)

	data, err := os.ReadFile(zipPath)
	if err != nil {
		return err
	}

	zr, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		return fmt.Errorf("opening zip: %w", err)
	}

	destDir := filepath.Dir(zipPath)
	for _, f := range zr.File {
		outPath := filepath.Join(destDir, f.Name)
		fmt.Printf("Extracted: %s\n", outPath)

		rc, err := f.Open()
		if err != nil {
			return err
		}
		defer rc.Close()

		out, err := os.Create(outPath)
		if err != nil {
			return err
		}
		defer out.Close()

		if _, err := io.Copy(out, rc); err != nil {
			return err
		}
	}
	return nil
}

func main() {
	dateStr := "05-11-2026"
	if len(os.Args) > 1 {
		dateStr = os.Args[1]
	}

	zipPath, err := downloadBhavcopy(dateStr)
	if err != nil {
		log.Fatal(err)
	}
	if zipPath == "" {
		return // holiday/weekend
	}

	if err := extractZip(zipPath); err != nil {
		log.Fatal("Extract error:", err)
	}
}

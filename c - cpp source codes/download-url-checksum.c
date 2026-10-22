/*use-clang-win - Alias in Poweshell Before Compilation as under:
clang.exe -O2 -o D:\dev\download-url-checksum.exe D:\dev\download-url-checksum.c */

#define _CRT_SECURE_NO_WARNINGS
#define WIN32_LEAN_AND_MEAN
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <windows.h>

#define CHUNK (4 * 1024 * 1024)

typedef unsigned char BYTE;
#include <bcrypt.h>
#pragma comment(lib, "bcrypt.lib")


/* ── Process helpers ──────────────────────────────────────────────────── */
static int run_process(const char *cmd) {
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si,sizeof(si)); si.cb=sizeof(si);
    ZeroMemory(&pi,sizeof(pi));
    char buf[4096];
    strncpy(buf,cmd,sizeof(buf)-1); buf[sizeof(buf)-1]='\0';
    if(!CreateProcessA(NULL,buf,NULL,NULL,TRUE,0,NULL,NULL,&si,&pi)){
        fprintf(stderr,"CreateProcess failed for: %s\n",cmd);
        return -1;
    }
    WaitForSingleObject(pi.hProcess,INFINITE);
    DWORD code=1;
    GetExitCodeProcess(pi.hProcess,&code);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return (int)code;
}

/* ── WARP ─────────────────────────────────────────────────────────────── */
static void warp_connect(void) {
    printf("Connecting WARP...\n");
    run_process("warp-cli connect");
    Sleep(3000);
    printf("WARP connected.\n");
}
static void warp_disconnect(void) {
    printf("Disconnecting WARP...\n");
    run_process("warp-cli disconnect");
    printf("WARP disconnected.\n");
}

/* atexit guarantees disconnect even on early exit */
static void warp_atexit(void) { warp_disconnect(); }

/* ── aria2c ───────────────────────────────────────────────────────────── */
#define ARIA2C_PATH "D:\\Programs\\msys64\\ucrt64\\bin\\aria2c.exe"

static const char *find_aria2c(void) {
    if(GetFileAttributesA(ARIA2C_PATH)!=INVALID_FILE_ATTRIBUTES)
        return ARIA2C_PATH;
    /* fall back to PATH */
    static char found[MAX_PATH];
    if(SearchPathA(NULL,"aria2c","exe",MAX_PATH,found,NULL))
        return found;
    return NULL;
}

static int do_download(const char *url, const char *folder) {
    const char *aria2c = find_aria2c();
    if(!aria2c){ fprintf(stderr,"aria2c not found.\n"); return 1; }

    /* extract filename from URL */
    const char *slash = strrchr(url,'/');
    const char *fname = (slash && slash[1]) ? slash+1 : "downloaded_file";

    char cmd[8192];
    snprintf(cmd,sizeof(cmd),
        "\"%s\" --split=4 --max-connection-per-server=4 "
        "--min-split-size=10M --file-allocation=none "
        "--max-tries=5 --retry-wait=3 "
        "--console-log-level=notice --summary-interval=5 "
        "--dir \"%s\" --out \"%s\" \"%s\"",
        aria2c, folder, fname, url);

    printf("Downloading: %s\n  -> %s\\%s\n", url, folder, fname);
    int rc = run_process(cmd);
    if(rc!=0){ fprintf(stderr,"aria2c exited with code %d\n",rc); return rc; }
    printf("Download complete.\n");
    return 0;
}

static int do_git_clone(const char *url, const char *folder) {
    char cmd[4096];
    snprintf(cmd,sizeof(cmd),"git clone \"%s\" \"%s\"",url,folder);
    printf("Cloning: %s\n  -> %s\n",url,folder);
    int rc = run_process(cmd);
    if(rc!=0){ fprintf(stderr,"git clone exited with code %d\n",rc); return rc; }
    printf("Clone complete.\n");
    return 0;
}

/* ── Checksum ─────────────────────────────────────────────────────────── */

static int verify_checksum(const char *filepath, const char *expected) {
    BCRYPT_ALG_HANDLE  hAlg  = NULL;
    BCRYPT_HASH_HANDLE hHash = NULL;
    NTSTATUS status;
    int rc = 1;

    status = BCryptOpenAlgorithmProvider(&hAlg, BCRYPT_SHA256_ALGORITHM, NULL, 0);
    if(!BCRYPT_SUCCESS(status)){ fprintf(stderr,"BCryptOpenAlgorithmProvider failed\n"); return 1; }

    status = BCryptCreateHash(hAlg, &hHash, NULL, 0, NULL, 0, 0);
    if(!BCRYPT_SUCCESS(status)){ fprintf(stderr,"BCryptCreateHash failed\n"); goto done; }

    FILE *fp = fopen(filepath, "rb");
    if(!fp){ fprintf(stderr,"Cannot open for checksum: %s\n", filepath); goto done; }

    _fseeki64(fp, 0, SEEK_END);
    long long total = _ftelli64(fp);
    _fseeki64(fp, 0, SEEK_SET);

    BYTE *buf = (BYTE*)malloc(CHUNK);
    long long done2 = 0;
    size_t n;
    while((n = fread(buf, 1, CHUNK, fp)) > 0){
        BCryptHashData(hHash, buf, (ULONG)n, 0);
        done2 += n;
        fprintf(stderr, "\r  Hashing: %.1f / %.1f MB (%.0f%%)",
                done2/1048576.0, total/1048576.0, done2*100.0/total);
    }
    fprintf(stderr, "\n");
    free(buf);
    fclose(fp);

    BYTE hash[32];
    BCryptFinishHash(hHash, hash, 32, 0);

    char hex[65];
    for(int i = 0; i < 32; i++) sprintf(hex+i*2, "%02x", hash[i]);
    hex[64] = '\0';
    printf("SHA256: %s\n", hex);

    if(expected && expected[0]){
        char exp[65]; 
        strncpy(exp, expected, 64); 
        exp[64] = '\0';
        for(int i = 0; exp[i]; i++)
            if(exp[i] >= 'A' && exp[i] <= 'Z') exp[i] += 32;
        if(strcmp(hex, exp) == 0){
            printf("OK - checksum matches.\n"); rc = 0;
        } else {
            printf("MISMATCH\n  expected: %s\n  got:      %s\n", exp, hex); rc = 2;
        }
    } else {
        rc = 0;
    }

done:
    if(hHash) BCryptDestroyHash(hHash);
    if(hAlg)  BCryptCloseAlgorithmProvider(hAlg, 0);
    return rc;
}

/* ── Prompt helper ────────────────────────────────────────────────────── */
static void prompt(const char *label, char *out, int len) {
    printf("%s: ", label);
    fflush(stdout);
    if(!fgets(out,len,stdin)) out[0]='\0';
    /* strip trailing newline */
    int l=(int)strlen(out);
    while(l>0&&(out[l-1]=='\n'||out[l-1]=='\r')) out[--l]='\0';
}

/* ── main ─────────────────────────────────────────────────────────────── */
int main(void) {
    char input[2048];   /* URL or "git clone <url>" */
    char folder[1024];
    char checksum[128];

    printf("=== Downloader + Checksum ===\n\n");
    prompt("Enter URL or 'git clone <url>'", input, sizeof(input));
    prompt("Destination folder",             folder, sizeof(folder));
    prompt("Expected SHA256 (leave blank to skip)", checksum, sizeof(checksum));

    /* determine mode */
    int is_clone = (strncmp(input,"git clone ",10)==0 ||
                    strncmp(input,"git clone \"",11)==0);
    const char *url = is_clone ? input+10 : input;
    /* strip leading spaces after "git clone " */
    while(*url==' ') url++;

    /* create destination folder */
    CreateDirectoryA(folder, NULL);

    /* connect WARP and register disconnect-on-exit */
    warp_connect();
    atexit(warp_atexit);

    int rc = 0;
    if(is_clone) {
        rc = do_git_clone(url, folder);
    } else {
        /* build filepath once, reuse for existence check + checksum */
        char url_clean[2048];
        strncpy(url_clean, url, sizeof(url_clean)-1);
        url_clean[sizeof(url_clean)-1] = '\0';
        char *q = strchr(url_clean, '?');
        if(q) *q = '\0';

        const char *slash = strrchr(url_clean, '/');
        const char *fname = (slash && slash[1]) ? slash+1 : "downloaded_file";

        char filepath[2048];
        snprintf(filepath, sizeof(filepath), "%s\\%s", folder, fname);

        /* check if fully downloaded already (no .aria2 control file present) */
        char aria2_ctrl[2100];
        snprintf(aria2_ctrl, sizeof(aria2_ctrl), "%s.aria2", filepath);

        if(GetFileAttributesA(filepath) != INVALID_FILE_ATTRIBUTES &&
           GetFileAttributesA(aria2_ctrl) == INVALID_FILE_ATTRIBUTES) {
            printf("File already exists, skipping download: %s\n", filepath);
            rc = 0;
        } else {
            if(GetFileAttributesA(aria2_ctrl) != INVALID_FILE_ATTRIBUTES)
                printf("Resuming incomplete download...\n");
            rc = do_download(url, folder);
        }

        /* checksum */
        if(rc==0 && checksum[0]){
            printf("Verifying: %s\n", filepath);
            rc = verify_checksum(filepath, checksum);
        }
    }
    
    /* atexit will call warp_disconnect automatically */
    return rc;
}

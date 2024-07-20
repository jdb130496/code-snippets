Add-Type -AssemblyName System.Windows.Forms
Add-Type -MemberDefinition @"
[DllImport("user32.dll")]
public static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
[DllImport("user32.dll")]
public static extern bool UnregisterHotKey(IntPtr hWnd, int id);
"@ -Name "Win32" -Namespace "Win32"

$null = [Win32.Win32]::RegisterHotKey([IntPtr]::Zero, 1, 0x0001, 0x73)

for ($i=0; $i -lt 10000; $i++) {
    $app = Start-Process "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\OpenOffice 4.1.14\OpenOffice Calc"
    Start-Sleep -Seconds 6
    for ($j=1; $j -le 30; $j++) {
        for ($k=1; $k -le 200; $k++) {
            Start-Sleep -Seconds 2
            [System.Windows.Forms.SendKeys]::SendWait($k.ToString())
            if ($k -lt 200) {
                [System.Windows.Forms.SendKeys]::SendWait("{DOWN}")
            }
            if ([System.Windows.Forms.Control]::ModifierKeys -band [System.Windows.Forms.Keys]::Alt) {
                if ([System.Windows.Forms.Control]::IsKeyLocked([System.Windows.Forms.Keys]::F4)) {
                    exit
                }
            }
        }
        [System.Windows.Forms.SendKeys]::SendWait("{RIGHT}")
        for ($l=1; $l -le 199; $l++) {
            [System.Windows.Forms.SendKeys]::SendWait("{UP}")
        }
    }
    Start-Sleep -Seconds 2
    [System.Windows.Forms.SendKeys]::SendWait("%{F4}")
    Start-Sleep -Seconds 2
    [System.Windows.Forms.SendKeys]::SendWait("{D}")
    Start-Sleep -Seconds 4
}

$null = [Win32.Win32]::UnregisterHotKey([IntPtr]::Zero, 1)


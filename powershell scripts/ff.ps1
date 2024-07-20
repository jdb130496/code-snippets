Add-Type -AssemblyName System.Windows.Forms
for ($i=0; $i -lt 10000; $i++) {
    $app = Start-Process "C:\windows\notepad.exe"
    Start-Sleep -Seconds 4
    [void][System.Reflection.Assembly]::LoadWithPartialName("Microsoft.VisualBasic") 
    [System.Windows.Forms.SendKeys]::SendWait("search by google")
    Start-Sleep -Seconds 10
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    Start-Sleep -Seconds 2
    [System.Windows.Forms.SendKeys]::SendWait("%{F4}")
    Start-Sleep -Seconds 2
    [System.Windows.Forms.SendKeys]::SendWait("{n}")
    Start-Sleep -Seconds 4
}

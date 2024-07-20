add-type -AssemblyName microsoft.VisualBasic
add-type -AssemblyName System.Windows.Forms
[system.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") | out-null
Add-Type -MemberDefinition '[DllImport("user32.dll")] public static extern void mouse_event(int flags, int dx, int dy, int cButtons, int info);' -Name U32 -Namespace W;
    $wsh = New-Object -ComObject Wscript.Shell
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(400,400);
    for (($i = 0); $i -lt 100000; $i++) {
    for (($j = 0); $j -lt 1; $j++) {	    
    $x = $y = $(Get-Random -Minimum 400 -Maximum 600);
    [Windows.Forms.Cursor]::Position = "$x,$y";
    echo $x;
    echo $y;
$wsh.AppActivate("[No Name] - GVIM")
Start-Sleep 2 
    [W.U32]::mouse_event(6,0,0,0,0);
$wsh.SendKeys("{TAB}");
    echo $j
$x = $y = $(Get-Random -Minimum 300 -Maximum 600);
    [Windows.Forms.Cursor]::Position = "$x,$y";
    echo $x;
    echo $y;
$wsh.AppActivate("powershell")
Start-Sleep 2
    [W.U32]::mouse_event(6,0,0,0,0);
$wsh.Sendkeys("{TAB}")
    echo $j
    Start-Sleep -s 1;	
    }
    Start-Sleep -s 1;
    }	

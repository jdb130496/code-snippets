function Get-ExeTargetMachine {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )
    $MACHINE_OFFSET = 4
    $PE_POINTER_OFFSET = 60
    $data = New-Object -TypeName System.Byte[] -ArgumentList 4096
    $stream = New-Object -TypeName System.IO.FileStream -ArgumentList ($FilePath, 'Open', 'Read')
    $stream.Read($data, 0, 4096) | Out-Null
    $PE_HEADER_ADDR = [System.BitConverter]::ToInt32($data, $PE_POINTER_OFFSET)
    $machineUint = [System.BitConverter]::ToUInt16($data, $PE_HEADER_ADDR + $MACHINE_OFFSET)
    $stream.Close()
    switch ($machineUint) {
        0x014c { "x86" }
        0x8664 { "x64" }
        default { "Unknown" }
    }
}


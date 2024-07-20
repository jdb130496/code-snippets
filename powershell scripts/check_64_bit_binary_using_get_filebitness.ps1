function Get-FileBitness {
    [CmdletBinding (SupportsShouldProcess=$True,DefaultParameterSetName="None")]
    PARAM (
        [Parameter (
            HelpMessage = "Enter binary file (s) to examine",
            Position = 0,
            Mandatory = $true,
            ValueFromPipeline = $true,
            ValueFromPipelineByPropertyName = $true
        )]
        [ValidateNotNullOrEmpty ()]
        [ValidateScript ( {Test-Path $_.FullName})]
        [IO.FileInfo []]
        $Path
    )
 
    BEGIN {
        # PE Header machine offset
        [int32]$MACHINE_OFFSET = 4
        # PE Header pointer offset
        [int32]$PE_POINTER_OFFSET = 60
        # Initial byte array size
        [int32]$PE_HEADER_SIZE = 4096
    }
 
    PROCESS {
        # Create a location to place the byte data
	[byte[]]$BYTE_ARRAY = New-Object -TypeName System.Byte[] -ArgumentList @($PE_HEADER_SIZE)
	        
        # Open the file for read access
        $FileStream = New-Object -TypeName System.IO.FileStream -ArgumentList ($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read)
        # Read the requested byte length into the byte array
        $FileStream.Read($BYTE_ARRAY, 0, $BYTE_ARRAY.Length) | Out-Null
[int32]$PE_HEADER_ADDR = [System.BitConverter]::ToInt32($BYTE_ARRAY, $PE_POINTER_OFFSET) 
        try {
            [int32]$machineUint = [System.BitConverter]::ToUInt16($BYTE_ARRAY, $PE_HEADER_ADDR + $MACHINE_OFFSET)
        } catch {
            $machineUint = 0xffff
        }
 
        switch ($machineUint) {
            0x0000 {return 'UNKNOWN'}
            0x0184 {return 'ALPHA'}
            0x01d3 {return 'AM33'}
            0x8664 {return 'AMD64'}
            0x01c0 {return 'ARM'}
            0x01c4 {return 'ARMNT'} # aka ARMV7
            0xaa64 {return 'ARM64'} # aka ARMV8
            0x0ebc {return 'EBC'}
            0x014c {return 'I386'}
            0x014d {return 'I860'}
            0x0200 {return 'IA64'}
            0x0268 {return 'M68K'}
            0x9041 {return 'M32R'}
            0x0266 {return 'MIPS16'}
            0x0366 {return 'MIPSFPU'}
            0x0466 {return 'MIPSFPU16'}
            0x01f0 {return 'POWERPC'}
            0x01f1 {return 'POWERPCFP'}
            0x01f2 {return 'POWERPCBE'}
            0x0162 {return 'R3000'}
            0x0166 {return 'R4000'}
            0x0168 {return 'R10000'}
            0x01a2 {return 'SH3'}
            0x01a3 {return 'SH3DSP'}
            0x01a6 {return 'SH4'}
            0x01a8 {return 'SH5'}
            0x0520 {return 'TRICORE'}
            0x01c2 {return 'THUMB'}
            0x0169 {return 'WCEMIPSV2'}
            0xffff {return 'INVALID'}
        }
    }
 
    END {
        $FileStream.Close()
        $FileStream.Dispose()
    }
}


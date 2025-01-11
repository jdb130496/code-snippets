Set objWMIService = GetObject(“winmgmts:\\” & strComputer & “\root\cimv2”)
Set colDevices = objWMIService.ExecQuery _
   (“Select * From Win32_USBControllerDevice”)

For Each objDevice in colDevices
   strDeviceName = objDevice.Dependent
   strQuotes = Chr(34)
   strDeviceName = Replace(strDeviceName, strQuotes, “”)
   arrDeviceNames = Split(strDeviceName, “=”)
   strDeviceName = arrDeviceNames(1)
   Set colUSBDevices = objWMIService.ExecQuery _
       (“Select * From Win32_PnPEntity Where DeviceID = ‘” & strDeviceName & “‘”)
   For Each objUSBDevice in colUSBDevices
       Wscript.Echo objUSBDevice.Description
       WScript.Echo objUSBDevice.PnPDeviceID ‘ Changed from Description to PnPDeviceID
                                 ‘as this script can be altered to return any property
                                 ‘of the Win32_USBControllerDevice collection.
   Next   
Next

This script does a query to get

import configparser
import sys

# Initialize the ConfigParser with case sensitivity
config = configparser.RawConfigParser()
config.optionxform = str

# Read the existing module.ini file
config.read(sys.argv[1])

# Add the new key-value pair to the WFClient section
config['WFClient']['DesktopApplianceMode'] = 'True'

# Update the value of CDViewerScreen to TRUE
config['WFClient']['CDViewerScreen'] = 'TRUE'

# Write the changes back to the module.ini file
with open('module.ini', 'w') as configfile:
    config.write(configfile)


# Existing and new values for VirtualDriver
existing_values = config['ICA 3.0']['VirtualDriver']
new_values = 'SpeechMikeAudio, PSPDPM, SpeechMikeMixer, SpeechMike, PSPHID, CiscoMeetingsVirtualChannel, CiscoTeamsVirtualChannel, HDXRTME, CiscoVirtualChannel, Imprivata, FTCtxBr, ZoomMedia'

# Combine existing and new values, removing duplicates
updated_values = existing_values.split(', ') + new_values.split(', ')
updated_values = ', '.join(sorted(set(updated_values), key=updated_values.index))

# Update the VirtualDriver key with the combined values
config['ICA 3.0']['VirtualDriver'] = updated_values

# Write the changes back to the module.ini file
with open('module.ini', 'w') as configfile:
    config.write(configfile)

# Add new values under ICA 3.0 section
config['ICA 3.0']['ZoomMedia'] = 'Off'
config['ICA 3.0']['PSPHID'] = 'On'
config['ICA 3.0']['PSPDPM'] = 'Off'
config['ICA 3.0']['SpeechMikeMixer'] = 'On'
config['ICA 3.0']['SpeechMike'] = 'Off'
config['ICA 3.0']['SpeechMikeAudio'] = 'On'
config['ICA 3.0']['FTCtxBr'] = 'Off'
config['ICA 3.0']['Imprivata'] = 'Off'
config['ICA 3.0']['CiscoTeamsVirtualChannel'] = 'On'
config['ICA 3.0']['CiscoMeetingsVirtualChannel'] = 'Off'
config['ICA 3.0']['CiscoVirtualChannel'] = 'Off'
config['ICA 3.0']['HDXRTME'] = 'Off'
config['ICA 3.0']['VDWEBRTC'] = 'Off'

# Write the changes back to the module.ini file
with open('module.ini', 'w') as configfile:
    config.write(configfile)

# Add and Update values in ClientAudio
config['ClientAudio']['AudioLatencyControlEnabled'] = 'TRUE'
config['ClientAudio']['EnableUDPAudio'] = 'TRUE'
config['ClientAudio']['UDPAudioPortLow'] = '16500'
config['ClientAudio']['UDPAudioPortHigh'] = '16509'
config['ClientAudio']['AudioMaxLatency'] = '300ms'
config['ClientAudio']['AudioLatencyCorrectionInterval'] = '300ms'

# Write the changes back to the module.ini file
with open('module.ini', 'w') as configfile:
    config.write(configfile)

# Add new section [GenericUSB]
config['GenericUSB'] = {'DriverName': 'VDGUSB.DLL'}

# Add new section [FTCtxBr]
config['FTCtxBr'] = {'DriverName': 'FTCTXBR.DLL', 'LogLevel':1}

# Add new section [CiscoVirtualChannel]
config['CiscoVirtualChannel'] = {'DriverName': 'VDCISCO.DLL'}

# Add new section [Imprivata]
config['Imprivata'] = {'DriverName': 'vdimp.dll'}

# Add new section [HDXRTME]
config['HDXRTME'] = {'DriverName': 'HDXRTME.so'}

# Add new section [CiscoMeetingsVirtualChannel]
config['CiscoMeetingsVirtualChannel'] = {'DriverName': 'libCiscoMeetingsCitrixPlugin.so'}

# Add new section [CiscoTeamsVirtualChannel]
config['CiscoTeamsVirtualChannel'] = {'DriverName': 'libCiscoTeamsCitrixPlugin.so'}

# Add new section [ZoomMedia]
config['ZoomMedia'] = {'DriverName': 'ZoomMedia.so'}

# Add new section [SpeechMike]
config['SpeechMike'] = {
    'DriverName': 'VDPSPCTR.dll',
    'LIB_DIR': '/opt/Citrix/ICAClient/SpMikeLib',
    'LIB_NAME': 'libCtxSpMike.so',
    'HIDDEV_DIR':'/dev/usb/',
    'JOYDEV_DIR':'/dev/input/',
    'FCBUTTON1':'12',
    'FCBUTTON2':'4',
    'FCBUTTON3':'14',
    'FCBUTTON4':'10'
    }
# Add new section [SpeechMikeAudio]
config['SpeechMikeAudio'] = {
    'DriverName': 'VDPSPAUD.dll',
    'LIB_DIR': '/opt/Citrix/ICAClient/SpMikeLib',
    'LIB_NAME': 'libCtxSbExtAlsa.so',
    'FORCE_PCM': '0'
    }
# Add new section [SpeechMikeMixer]
config['SpeechMikeMixer'] = {
    'DriverName': 'VDPSPMIX.dll',
    'LIB_DIR': '/opt/Citrix/ICAClient/SpMikeLib',
    'LIB_NAME': 'libCtxMixerAlsa.so',
    'DELAY_SET': '0'
    }
# Add new section [PSPDPM]
config['PSPDPM'] = {
    'DriverName': 'VDPSPDPM.dll',
    'LIB_DIR': '/opt/Citrix/ICAClient/SpMikeLib',
    'LIB_NAME': 'libCtxHidMan.so',
    'DPM_DIR': '/tmp/PhilipsDPM',
    'DPM_DRIVE': '"P:\\"'
    }

# Add new section [PSPHID]
config['PSPHID'] = {
    'DriverName': 'VDPSPHID.dll',
    'LIB_DIR': '/opt/Citrix/ICAClient/SpMikeLib',
    'LIB_NAME': 'libCtxHIDManagerRemoteClient.so'
    }

# Write the changes back to the module.ini file
with open('module.ini', 'w') as configfile:
    config.write(configfile)

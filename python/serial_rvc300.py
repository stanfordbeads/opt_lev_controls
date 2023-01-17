import pyvisa as pyvisa

### GROSS HARD-CODED INSTRUMENT NAME CAUSE THE RVC300 IS 
### DUMB AND DOESN'T RECOGNIZE THE IEEE DEFAULT COMMAND
### "*IDN?" SO WE CAN'T EASILY LOOP AND FIND IT BY 
### QUERYING THE SERIAL INSTRUMENTS
# rvc300_resource_name = 'ASRL8::INSTR'
rvc300_resource_name = None

rvc300_firmware_string = 'VER=2.11'
evr116_valve_string = 'VAV=116'



def _process_pressure_string(pressure_string):
    '''
    Parse the string with the pressure value reported by the RVC300.
    Unlikely to change but this keeps the behavior consistent 
    across any functions that handle this value.
    '''

    pressure_value = float(pressure_string[4:-4])
    pressure_units = pressure_string[-4:]

    return pressure_value, pressure_units



def _process_flow_string(flow_string):
    '''
    Parse the string with the flow value reported by the RVC300.
    Unlikely to change but this keeps the behavior consistent 
    across any functions that handle this value.
    '''

    flow_value = float(flow_string[4:-7])
    flow_units = flow_string[-7:]

    return flow_value, flow_units



def _setup_serial_rvc300(resource):
    '''
    Setup the standard communication settings for the RVC300.
    '''

    ### Set communication protocols
    resource.baud_rate = 9600
    resource.flow_control = pyvisa.constants.ControlFlow.none
    resource.parity = pyvisa.constants.Parity.none

    return resource



def _find_rvc300(verbose=True):
    '''
    Function to loop over the available serial interfaces, trying to find
    the RVC300 and EVR116 controller/valve combo by using some of the 
    firmware version and valve indentification functions detailed in the
    Pfeiffer manual

    INPUT:

        verbose - boolean, Whethere to print any debugging messages or not

    '''

    global rvc300_resource_name
    if rvc300_resource_name is not None:
        return None

    rm = pyvisa.ResourceManager()

    for resource_name in rm.list_resources():

        ### Ignore everything but the serial interfaces
        if 'ASRL' not in resource_name:
            continue

        firmware = False
        valve = False

        ### Try to open the serial resource first with its own try/except
        ### block since resources that are currently in use may raise 
        ### errors (I haven't tested ANYTHING besides the serial resource
        ### associated to the controller so this is just a guess about
        ### what might happen)
        try:
            resource = rm.open_resource(resource_name)
        except:
            if verbose:
                print(f"Couldn't open: <{resource_name}>")
            continue

        ### Define the default communication settings
        resource = _setup_serial_rvc300(resource)

        ### If a visa session could be established, query the instrument
        ### for the firmware version and valve type, which are hopefully
        ### unique to this controller!
        try:    
            if rvc300_firmware_string in resource.query('VER?').strip():
                firmware = True
            if evr116_valve_string in resource.query('VAV?').strip():
                valve = True
            resource.close()

            ### If everything matches up, define the global resource name
            ### for the controller
            if firmware:
                rvc300_resource_name = resource_name

            ### Print a message if the valve was also found
            if firmware and valve:
                if verbose:
                    print(f'Found RVC300 and EVR116 at: <{resource_name}>')
                break
            ### Let the user know if we found the controller (i.e. the 
            ### firmware query made sense), but not the leak valve. 
            ### Don't break the loop just yet in case multiple
            ### controller units are hooked up to the computer but only
            ### one has the valve
            elif firmware and not valve:
                if verbose:
                    print(f'Found RVC300 controller at: <{resource_name}>,'\
                           + ' but no leak valve')


        except:
            if verbose:
                print("'VAV?' and/or 'VER?' commands raise "\
                       + f"errors for: <{resource_name}>")
            resource.close()
            continue

    ### Raise an error if we couldn't find the controller we wanted
    if rvc300_resource_name is None:
        raise IOError("Couldn't find RVC300 serial interface")

    return None



def get_pressure():
    '''
    Command to query the pressure, assuming a gauge is hooked up
    and operating
    '''

    ### Find the leak valve name if we haven't already
    global rvc300_resource_name
    _find_rvc300()

    ### Establish the VISA session
    rm = pyvisa.ResourceManager()
    rvc300 = rm.open_resource(rvc300_resource_name)

    ### Query the pressure and close the VISA session
    pressure_string = rvc300.query("PRS?").strip()
    rvc300.close()

    pressure_value, pressure_units = \
        _process_pressure_string(pressure_string)

    return pressure_value, pressure_units



def get_flow_rate():
    '''
    Command to query the flow rate in units of mbar * L / s, or 
    Torr * L / s (determined by a controller setting)
    '''

    ### Find the leak valve name if we haven't already
    global rvc300_resource_name
    _find_rvc300()

    ### Establish the VISA session
    rm = pyvisa.ResourceManager()
    rvc300 = rm.open_resource(rvc300_resource_name)

    ### Query the flow and close the VISA session
    flow_string = rvc300.query("FLO?").strip()
    rvc300.close()

    flow_value, flow_units = _process_flow_string(flow_string)

    return flow_value, flow_units



def set_flow_rate(flow_rate):
    '''
    Command to set flow rate in units of mbar * L / s, or Torr * L / s,
    where the units are determined by a controller setting only
    accessible via the front panel.

    INPUTS:

        flow_rate - float, desired flow rate

    '''

    ### Find the leak valve name if we haven't already
    global rvc300_resource_name
    _find_rvc300()

    ### Establish the VISA session
    rm = pyvisa.ResourceManager()
    rvc300 = rm.open_resource(rvc300_resource_name)

    ### Ensure that we're in Flow mode and that everything makes sense
    mode_string = rvc300.query("MOD=F").strip()
    assert "MOD=FLOW" in mode_string, "Valve not in 'FLOW' mode"

    ### Set the desired value
    command_string = f"FLO={flow_rate:0.2E}"
    command_result = rvc300.query(command_string).strip()
    rvc300.close()

    flow_value, flow_units = _process_flow_string(command_result)

    return flow_value, flow_units



def open_valve():
    '''
    Fully opens the leak valve.
    '''
    return set_flow_rate(1000.0)



def close_valve():
    '''
    Fully closes the leak valve.
    '''
    return set_flow_rate(1.0e-6)




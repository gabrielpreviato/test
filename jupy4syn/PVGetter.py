import time

# Widgets
import ipywidgets as widgets
from IPython.display import display

# EPICS and Py4Syn
from epics import PV, caget

# Jupy4Syn
from jupy4syn.utils import logprint
from jupy4syn.Configuration import Configuration


class PVGetter(widgets.Button):
    def __init__(self, name, config=Configuration(), *args, **kwargs):
        """
        **Constructor**

        Parameters
        ----------
        name : :obj:`str`
            Name of the PV (e.g. "IOC:m1") to get a value, or name of the mnemonic defined in 
            config.yml (e.g. "solm1") to get a value
        config : :py:class:`Configuration <jupy4syn.Configuration.Configuration>`, optional
            Configuration object that contains Jupyter Notebook runtime information, by default Configuration()
        
        Examples
        --------
        >>> config = Configuration()
        >>> config.display()
        >>> pv_getter = PVGetter(config)
        >>> pv_getter.display()
        """
        widgets.Button.__init__(self, *args, **kwargs)
        
        # Config
        self.config = config
        
        # PV associated to the button
        self.pv = PV(name)
        self.name = name

        # Check if name is a PV, if not search it in config.yml motors
        if not self.pv.wait_for_connection():
            if name in config.yml_motors:
                try:
                    self.pv = PV(config.yml_motors[name]['pv'])
                except KeyError:
                    raise ValueError('Motor %s doesn\'t have pv field' % name)
            elif name in config.yml_counters:
                try:
                    self.pv = PV(config.yml_counters[name]['pv'])
                except KeyError:
                    raise ValueError('Counter %s doesn\'t have pv field' % name)
            else:
                raise ValueError("Invalid name. Name provided is neither a conencted PV neither a config.yml mnemonic")

            # Check if PV is finally connected
            if not self.pv.wait_for_connection():
                raise Exception("Valid name, but PV connection not possible")


        self.pv_desc = caget(self.pv.pvname + ".DESC")
        self.pv_name = self.pv.pvname

        self.value = ""
        self.value_text = widgets.Label(self.value)
        
        # class Button values for PVSetter
        self.description = 'Get "' + self.pv_desc + '" value'
        self.disabled = False
        self.button_style = 'success'
        self.tooltip = 'Click me'
        self.icon = ''    
        
        # Set callback function for click event
        self.on_click(self._button_click)
        
        # Widgets Boxes
        self.output = widgets.Output()
        
    @staticmethod
    def _button_click(b):
        # Clear previous logs outputs
        b.output.clear_output()
        
        # with statement to output logs in stdou (if this option is enabled)
        with b.output:
            # Change button to a "clicked status"
            b.disabled = True
            b.button_style = ''

            # We should sleep for some time to give some responsiveness to the user
            time.sleep(0.5)

            logprint("Getting PV " + b.pv_name + " value", config=b.config)
            try:
                # Move the motor to target absolute position
                b.value = b.pv.get()
                b.value_text.value = "Value of " + b.name + " is " + str(b.value)
                logprint("Get value of PV " + b.pv_name, config=b.config)
            except Exception as e:
                # If any error occurs, log that but dont stop code exection
                logprint("Error in Getting value " + b.bounded_text.value + " of PV " + b.pv_name, "[ERROR]", config=b.config)
                logprint(str(e), "[ERROR]", config=b.config)

            # Change button layout back to normal
            b.disabled = False
            b.button_style = 'success'
        
    def display(self):
        display(self,
                self.value_text,
                self.output
        )

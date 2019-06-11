# Widgets
import ipywidgets as widgets
from IPython.display import display

# EPICS and Py4Syn
from epics import PV, caget

# Jupy4Syn
from .utils import logprint
from .Configuration import Configuration


class PVSetter(widgets.Button):
    def __init__(self, pv_name, config=Configuration(), *args, **kwargs):
        """ The PVSetter uses Jupyter button widgets to set PV values

        The PVSetter class provides an ipywidgets interface to help changing and PV value
        using a Jupyter Notebook. It shows a text box that is used to get the value to be
        set in the PV and a button to change the PV value to the value written in the text box.

        Arguments:
            pv_name {[str]} -- Name of the PV to be set a value
        
        Keyword Arguments:
            config {[Configuration]} -- Configuration object that contains Jupyter Notebook runtime information
            (default: {Configuration()})
        """
        widgets.Button.__init__(self, *args, **kwargs)
        
        # Config
        self.config = config
        
        # PV associated to the button
        self.pv = PV(pv_name)
        self.pv_desc = caget(pv_name + ".DESC")
        self.pv_name = pv_name
        
        # Bounded float text associated to the button
        self.bounded_text = widgets.Text(
                                value=str(self.pv.value),
                                description=self.pv_desc,
                                disabled=False
                              )
        
        # class Button values for PVSetter
        self.description = 'Set "' + self.pv_desc + '" value'
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

            logprint("Setting PV " + b.pv_name + " to value " + b.bounded_text.value, config=b.config)
            try:
                # Move the motor to target absolute position
                b.pv.put(b.bounded_text.value, wait=False)
                logprint("Set value " + b.bounded_text.value + " to PV " + b.pv_name, config=b.config)
            except Exception as e:
                # If any error occurs, log that but dont stop code exection
                logprint("Error in setting value " + b.bounded_text.value + " to PV " + b.pv_name, "[ERROR]", config=b.config)
                logprint(str(e), "[ERROR]", config=b.config)

            # Change button layout back to normal
            b.disabled = False
            b.button_style = 'success'
        
    def display(self):
        display(widgets.HBox([self.bounded_text, self]),
                self.output
        )
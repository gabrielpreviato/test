import ipywidgets as widgets
from IPython.display import display
import time
import subprocess
from .utils import logprint


class ManualAlignmentButton(widgets.Button):
    
    def __init__(self, config, *args, **kwargs):
        widgets.Button.__init__(self, *args, **kwargs)
        
        # Config
        self.config = config
        
        # class Button values for MonitorScanSave
        self.description = 'Start Manual Alignment'
        self.disabled = False
        self.button_style = 'success'
        self.tooltip = 'Click me'
        self.icon = ''
        self.layout = widgets.Layout(width='300px')
        
        # Set callback function for click event
        self.on_click(self._click_button)
        
        # Logging
        self.output = widgets.Output()

        # Widgets display box
        self.display_box = widgets.VBox([self, self.output])
        
    @staticmethod
    def _click_button(b):
        # Clear previous logs outputs
        b.output.clear_output()
        
        # with statement to output logs in stdou (if this option is enabled)
        with b.output:
            # Change button to a "clicked status"
            b.disabled = True
            b.button_style = ''
            b.description='Aligning...'

            # Create a subprocess with the slits script from sol-widgets
            try:
                logprint("Starting manual alignment", config=b.config)
                subprocess.Popen(["slits"],
                                 shell=True)

                logprint("Finished manual alignment", config=b.config)
            except Exception as e:
                # If any error occurs, log that but dont stop code exection
                logprint("Error in manual alignment", "[ERROR]", config=b.config)
                logprint(str(e), "[ERROR]", config=b.config)

            # We should sleep for some time to give some responsiveness to the user
            time.sleep(1.0)

            # Reenable button
            b.disabled = False
            b.button_style = 'success'
            b.description='Start Manual Alignment'
    
    def display(self):
        display(self.display_box)

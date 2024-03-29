from pathlib import Path
import time

# Widgets
import ipywidgets as widgets
from IPython.display import display

# Jupy4Syn
from jupy4syn.Configuration import Configuration
from jupy4syn.JupyScan import JupyScan
from jupy4syn.utils import logprint


class ScanButton(widgets.Button):
    
    def __init__(self, config=Configuration(), *args, **kwargs):
        widgets.Button.__init__(self, *args, **kwargs)
        
        # Config
        self.config = config
        
        # Text box to write the motors to move
        self.text_motors = widgets.Textarea(
            value='',
            placeholder='Motors names from config.yml\nExample: solm3 gap2',
            description='',
            disabled=False
        )
        
        # Text box to write the configuration file
        self.text_config = widgets.Textarea(
            value='',
            placeholder='Name of the yml configuration file\nExample: default\n(PS: write "default" to load config.default.yml file)',
            description='',
            disabled=False
        )
        
        # Text box for start
        self.text_start = widgets.Text(
            value='',
            placeholder='Example for 2 motors: [1, 3], [7, 8]',
            description='',
            disabled=False
        )
        
        # Text box for end
        self.text_end = widgets.Text(
            value='',
            placeholder='Example for 2 motors: [2, 4], [8, 8.5]',
            description='',
            disabled=False
        )
        
        # Text box for step or points
        self.text_step_points = widgets.Text(
            value='',
            placeholder='Example for 2 motors: [1, 1], [0.5, 0.25]',
            description='',
            disabled=False
        )
        
        # Text box for time
        self.text_time = widgets.Text(
            value='',
            placeholder='Example for 2 motors: [1], [0.4]',
            description='',
            disabled=False
        )
        
        # Text box for output
        self.text_output = widgets.Text(
            value='',
            placeholder='Output file name, if left empty, file name will be the default name, "test"',
            description='',
            disabled=False
        )
        
        # Text box for optimum
        self.text_optimum = widgets.Text(
            value='',
            placeholder="Move motor to the optimal point according to \
                         this counter after scan. Leave empty for no move.",
            description='',
            disabled=True
        )
        
        # Optimum checkbox
        self.checkbox_optimum = widgets.Checkbox(
            value=False,
            description="",
            disabled=False,
            style={'description_width': 'initial'},
            layout = widgets.Layout(width='36px')
        )     

        self.checkbox_optimum.observe(self.change_checkbox_optimum, names=['value'])
        
        # class Button values for ScanButton
        self.description='Start Scan'
        self.disabled=False
        self.button_style='success'
        self.tooltip='Click me'
        self.icon=''
        self.layout = widgets.Layout(width='300px')
        
        # Boxes
        self.pv_values = {}
        
        # PVs
        self.motor_list = []
        
        # Set callback function for click event
        self.on_scan = False
        self.scan_ended = False
        self.config_loaded = False
        self.on_click(self._scan_button)
        
        # Main widget
        self.main_box = widgets.VBox([widgets.HBox([widgets.Label("Motors names", layout=widgets.Layout(width='150px')), self.text_motors]),
                                      widgets.HBox([widgets.Label("Configuration file name", layout=widgets.Layout(width='150px')), self.text_config]),
                                      widgets.HBox([widgets.Label("Start points", layout=widgets.Layout(width='150px')), self.text_start]),
                                      widgets.HBox([widgets.Label("End points", layout=widgets.Layout(width='150px')), self.text_end]),
                                      widgets.HBox([widgets.Label("Step or Points", layout=widgets.Layout(width='150px')), self.text_step_points]), 
                                      widgets.HBox([widgets.Label("Time", layout=widgets.Layout(width='150px')), self.text_time]),
                                      widgets.HBox([self.checkbox_optimum,
                                                    widgets.Label("Go to optimum of: ", layout=widgets.Layout(width='110px')),
                                                    self.text_optimum]),
                                      widgets.HBox([widgets.Label("Output file name", layout=widgets.Layout(width='150px')), self.text_output]),
                                      self])
        self.output = widgets.Output()

    
    def change_checkbox_optimum(self, change):
        self.text_optimum.disabled = not change.new
    
        
    @staticmethod
    def _scan_button(b):
        # Clear previous logs outputs
        b.output.clear_output()
        
        # with statement to output logs in stdout (if this option is enabled)
        with b.output:
            # Change button appearence
            b.description = 'Scanning'
            b.button_style = ''

            # Disable button to avoid double commands
            b.disabled = True

            # Disable box edition to avoid erros
            boxes = [b.text_motors, b.text_config, b.text_start, b.text_end, 
                    b.text_step_points, b.text_time, b.text_optimum, b.text_output]

            for box in boxes:
                box.disabled = True

            # Reset motor list
            b.motor_list = []

            # Get motors names from the text box
            motor_list_names = b.text_motors.value.split(' ')
            logprint("Scanning on motors" + ', '.join(motor_list_names), config=b.config)

            # Get config file name from the text box
            config_name = b.text_config.value
            logprint("YML config file: " + config_name, config=b.config)

            # Load scan parameters
            start = []
            end = []
            step_or_points = []
            time = []
            try:
                # Get lists from text boxes
                start = [eval(b.text_start.value)]
                end = [eval(b.text_end.value)]
                step_or_points = [eval(b.text_step_points.value)]
                time = [eval(b.text_time.value)]

                logprint("Loaded 'start, end, step or points, time' scan parameters", config=b.config)
            except Exception as e:
                # If any error occurs, log that but dont stop code exection
                logprint("Error loading 'start, end, step or points, time' scan parameters", "[ERROR]", config=b.config)
                logprint(str(e), "[ERROR]", config=b.config)

            # Get output file name
            output = b.text_output.value if b.text_output.value != '' else 'test'
            
            # Get absolute path to file, and create a scans directory if the directory doesn't exist
            mypath = Path().absolute() / 'scans'
            if not mypath.is_dir():
                mypath.mkdir()
            
            # Put the path to the output
            output = str(mypath) + '/' + output
            
            # Get optimum move option
#             optimum = b.text_optimum.value if b.checkbox_optimum.value else False
            optimum = False

            # Get sync option
            sync = False
            # Initiate scan
            try:
                js = JupyScan(motor_list_names, start, end, step_or_points, time, config_name, optimum, sync, output)
                
                js.run()
                logprint("Finished scan, output saved in file " + output, config=b.config)
            except Exception as e:
                # If any error occurs, log that but dont stop code exection
                logprint("Error in trying to scan", "[ERROR]", config=b.config)
                logprint(str(e), "[ERROR]", config=b.config)

            # Change button appearence
            b.description = 'Start Scan'
            b.button_style = 'success'

            # Re enable button
            b.disabled = False

            # Re enable box edition 
            for box in boxes:
                box.disabled = False
               

    def display(self):
        display(self.main_box, self.output)

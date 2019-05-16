import json
import os
import threading
import IPython
from IPython.display import display, update_display, Image
import ipywidgets as widgets
import time
import pandas as pd
import subprocess
from .utils import logprint
from pathlib import Path
from .ScanParser import ScanParser
import plotly.graph_objs as go
import plotly.io as pio
from plotly import tools


class MonitorScanSave(widgets.Button):
    
    def __init__(self, config, *args, **kwargs):
        widgets.Button.__init__(self, *args, **kwargs)
        
        # Config
        self.config = config     
        self.plots_list = config.plots_list
        
        # class Button values for MonitorScanSave
        self.description='Start Scanning Plot'
        self.disabled=False
        self.button_style='success'
        self.tooltip='Click me'
        self.icon=''
        self.layout = widgets.Layout(width='300px')
        
        # Scan save file and directory
        self.scan_save_dir = '/tmp/'
        self.scan_save_file = 'scan_gui.temp'
        self.stop_file = 'stop'

        self.scan_path = Path(self.scan_save_dir + self.scan_save_file)
        self.stop_path = Path(self.scan_save_dir + self.stop_file)
        
        # Logging
        self.output = widgets.Output()

        # Scan-gui process
        self.scan_gui_process = subprocess.Popen(["echo"])

        
        # Threading
        self.monitor = False
        self.thread = threading.Thread()
        self.refresh_thread = threading.Thread()
        self.interrupted_scan = False
        self.fig_thread = threading.Thread()
        
        # Set callback function for click event
        self.on_click(self._start_button)
        
        # Widgets displays
        self.start_button = widgets.VBox([self])
        
        # Clean previous temp config file
        try:
            os.remove(str(self.scan_path))
            os.remove(str(self.stop_path))
        except:
            pass
        
        self.checkbox_live_plot = widgets.Checkbox(
            value=False,
            description="Live plot in Jupyter: ",
            disabled=False,
            style={'description_width': 'initial'}
        )
        
        self.checkbox_final_plot_jupy = widgets.Checkbox(
            value=False,
            description="Plot with Plotly after scan ends: ",
            disabled=False,
            style={'description_width': 'initial'}
        )

        self.checkbox_final_plot_pyqt = widgets.Checkbox(
            value=True,
            description="Plot with PyQtGraph after scan ends: ",
            disabled=False,
            style={'description_width': 'initial'}
        )
        
        self.select_plot_option = widgets.Dropdown(
            options=['Plot after ends with PyQt', 'Plot after ends with Plotly', 'Live Plot'],
            value='Plot after ends with PyQt',
            # rows=10,
            description='',
            disabled=False,
            style={'description_width': 'initial'}
        )
        
        self.fig = go.FigureWidget()
        self.fig_box = widgets.Box()
        self.refresh_icon_box = widgets.Box(layout=widgets.Layout(width='40px', height='40px'))
        
        self.export = False
        self.clear_threads = False
        
    @staticmethod
    def _start_button(b):
        # Clear previous logs outputs
        b.output.clear_output()
        
        # with statement to output logs in stdou (if this option is enabled)
        with b.output:
            if b.monitor:
                # Enable checkboxes
                b.checkbox_live_plot.disabled = False
                b.checkbox_final_plot_jupy.disabled = False
                b.select_plot_option.disabled = False
                
                # Change button monitor status
                b.monitor = not b.monitor
                
                # Change button to a "clicked status"
                b.disabled = True
                b.button_style = ''
                b.description='Stopping...'
                
                # We should sleep for some time to give some responsiveness to the user
                time.sleep(0.5)

                # Stop thread to monitor the save file
                try:
                    logprint("Stopping threads", config=b.config)
                    b.thread.join()
                    b.fig_thread.join()
                    b.refresh_thread.join()
                    
                    b.clear_threads = False
                except Exception as e:
                    # If any error occurs, log that but dont stop code exection
                    logprint("Error in stopping threads", "[ERROR]", config=b.config)
                    logprint(str(e), "[ERROR]", config=b.config)

                # Change button layout monitoring
                b.disabled = False
                b.button_style = 'success'
                b.description='Start Scanning Plot'
            else:
                # Disable checkboxes
                b.checkbox_live_plot.disabled = True
                b.checkbox_final_plot_jupy.disabled = True
                b.select_plot_option.disabled = True
                
                if b.scan_gui_process.poll() is not None:
                    b.scan_gui_process = subprocess.Popen(["pydm --hide-nav-bar --hide-menu-bar ~/work/scan-gui/scan_gui.py"],
                                     shell=True)
                
                # Change button monitor status
                b.monitor = not b.monitor
                
                # Change button to a "clicked status"
                b.disabled = True
                b.button_style = ''
                b.description='Starting...'
                
                # We should sleep for some time to give some responsiveness to the user
                time.sleep(0.5)
                
                # Clean previous scans config
                try:
                    os.remove(str(b.scan_path))
                    os.remove(str(b.stop_path))
                except:
                    pass

                # Start thread to monitor the save file
                try:
                    logprint("Starting thread", config=b.config)
                    b.thread = threading.Thread(target=b.monitor_save_file)
                    b.thread.start()
                except Exception as e:
                    # If any error occurs, log that but dont stop code exection
                    logprint("Error in starting thread", "[ERROR]", config=b.config)
                    logprint(str(e), "[ERROR]", config=b.config)

                # Change button layout monitoring
                b.disabled = False
                b.button_style = 'danger'
                b.description='Stop Scanning Plot'
            
    
    def monitor_save_file(self):
        with self.output:
            while self.monitor:
                if self.scan_path.is_file():
                    # Started scan
                    self.started_scan = True
                    
                    with open(str(self.scan_path)) as file:
                        try: 
                             save_file = json.load(file)
                        except ValueError: 
                             pass
                    
                    os.remove(str(self.scan_path))
                    
                    try:
                        os.remove(str(self.stop_path))
                    except:
                        pass
                    
                    command = save_file["command"]["value"]
                    parser = self.scan_parser()
                    
                    self.synchronous = save_file["checkSync"]["value"]  
                    self.number_repeats = save_file["spinRepeat"]["value"]

                    # Waits for file creation by scan-gui
                    time.sleep(1.0)

                    self.scan_names = self.get_scan_name(command, parser, self.number_repeats)
                    config_name = self.get_config_name(command, parser)
                    
                    self.plot_name = self.scan_names[-1] + "-jupy.png"
                    
                    ts = time.gmtime()
    
                    year_month_day = time.strftime("%Y-%m-%d", ts)
                    time_stamp = time.strftime("%Y-%m-%d %H:%M:%S", ts) + " UTC-0"
                    self.log_str = time_stamp + "| [SCAN]:\n" + \
                              "Scan with command: '" + command + "' repeated " + str(self.number_repeats) + " times\n" + \
                              "Scan configuration: '" + config_name + "'\n" + \
                              "Scan data saved in: '" + self.scan_names[-1] + "'\n" + \
                              "Jupyter Scan plot saved in: '" + self.plot_name + "'\n" + \
                              "PyQtGraph Scan plot saved in: '" + self.scan_names[-1] + ".png" + "'\n"
                    
                    log_file_name = Path('./scanlogs/' + year_month_day + '-scanlog.txt')
                    with open(str(log_file_name), "a") as f:
                        f.write(self.log_str + '\n')
                    IPython.display.update_display(IPython.display.Pretty(self.log_str), display_id='text')
                                    
                    if self not in self.plots_list:
                        self.plots_list.append(self)

                    # Call live graph
                    self.list_motors = save_file["listMotors"]["value"]

                    self.fig_thread = threading.Thread(target=self.thread_plot)
                    self.fig_thread.start()
                    
                    # Scan status icon
                    self.refresh_thread = threading.Thread(target=self.thread_refresh_icon)
                    self.refresh_thread.start()  
                elif self.stop_path.is_file():
                    self.started_scan = False
                    self.interrupted_scan = True
                    self.clear_threads = True

                    os.remove(str(self.stop_path))
                else:
                    pass
                
                if self.clear_threads:
                    try:
                        self.fig_thread.join()
                        self.refresh_thread.join()
                    except:
                        pass
                    
                    self.clear_threads = False
                
                time.sleep(0.5)
                
    def get_scan_name(self, command, parser, number_repeats):
        args = parser.parse_known_args(command.split(' '))

        fileName = args[0].output

        scan_names = []

        leadingZeros = 4
        newName = ""
        cont = 0
        while(True):
            cont += 1
            newName = fileName + "_" + str(cont).zfill(leadingZeros)
            if(os.path.isfile(newName)):
                continue
            else:
                for i in range(number_repeats):
                    scan_names.append(fileName + "_" + str(cont - 1 + i).zfill(leadingZeros))
#                 if self.synchronous:
#                     newName = fileName + "_" + str(cont - 1).zfill(leadingZeros)
                break
                
        return scan_names
    
    def get_config_name(self, command, parser):
        args = parser.parse_known_args(command.split(' '))

        config_name = args[0].configuration
        
        return config_name
    
    def scan_parser(self):
        parser = ScanParser()
        
        return parser.parser
    
    def update_pd(self, default_names, label):
        dfs = []
        number_non_empty = len(default_names)

        for default_name in default_names:
            try:
                dfs.append(pd.read_csv(default_name, sep=' ', comment='#', header=None))
            except:
                dfs.append(pd.DataFrame())
                number_non_empty -= 1

        if number_non_empty == 0:
            return dfs, label

        filtered_label = label
        if not label:
            labels = []
            with open(default_names[0]) as file:
                for i, line in enumerate(file):
                    if i == 6:
                        self.number_reads = (int(line.split(' ')[1]))
                    elif i == 8:
                        labels = line.split(' ')[1:]
                        break

            labels = list(filter(lambda x: x != '', labels))

            for item in labels:
                filtered_label.append(item.rstrip('\n'))

            label = filtered_label

        for df in dfs:
            if not df.empty:
                df.columns = pd.Index(filtered_label, dtype='object')
        
        return dfs, label

    def thread_plot(self):
        dfs = []
        dfs.append(pd.DataFrame())
        while dfs[0].empty:
            label = []
            dfs, label = self.update_pd(self.scan_names, label)
        
        number_motors = len(self.list_motors)

        if self.select_plot_option.value == "Plot after ends with Plotly" or self.select_plot_option.value == "Live Plot":
            self.create_figure(len(dfs[0].columns) - number_motors)
            self.clear_image_file()
        
        while dfs[-1].shape[0] < self.number_reads:
            dfs, label = self.update_pd(self.scan_names, label)
            if self.select_plot_option.value == "Live Plot":
                for i in range(len(dfs)):
                    if dfs[i].empty:
                        continue

                    for j in range(len(dfs[i].columns) - number_motors): 
                        self.fig['data'][i + j*len(dfs)]['x'] = dfs[i].index.values
                        self.fig['data'][i + j*len(dfs)]['y'] = dfs[i][dfs[i].columns[number_motors + j]].values               

            time.sleep(1)
        
        # Finished scan
        self.started_scan = False
        self.clear_threads = True
        
        # update last scan value
        if self.select_plot_option.value == "Plot after ends with Plotly" or self.select_plot_option.value == "Live Plot":
            for i in range(len(dfs)):
                    if dfs[i].empty:
                        continue

                    for j in range(len(dfs[i].columns) - number_motors): 
                        self.fig['data'][i + j*len(dfs)]['x'] = dfs[i].index.values
                        self.fig['data'][i + j*len(dfs)]['y'] = dfs[i][dfs[i].columns[number_motors + j]].values                           
                
            # save image as png
            pio.write_image(self.fig, self.plot_name)
        
        # Plot scan-gui pyqt graph
        if self.select_plot_option.value == 'Plot after ends with PyQt':
            # Waits for scan-gui to save the plot
            time.sleep(5.0)

            self.load_image_file(self.scan_names[-1] + ".png")
            
    def create_figure(self, number_traces):
        self.traces = []
        
        self.fig = go.FigureWidget(tools.make_subplots(rows=number_traces, cols=1))
        
        for i in range(number_traces):
            self.traces.append([])

            for _ in range(len(self.scan_names)):
                trace = go.Scatter(
                    x=[], y=[], # Data
                    mode='lines+markers', name='line' + str(i+1)
                )

                self.traces[i].append(trace)
                self.fig.append_trace(trace, i + 1, 1) # using i + 1 because plot index starts at 1

        self.fig['layout'].update(title='Scan', plot_bgcolor='rgb(230, 230, 230)')
        self.fig_box.children = (self.fig,)
        
    def thread_refresh_icon(self):
        self.refresh_icon_box.layout = widgets.Layout(width='40px', height='40px')
        
        file = open(".img/refresh_00.png", "rb")
        image = file.read()
        img_w = widgets.Image(
            value=image,
            format='png',
            width=35,
            height=35,
        )
        
        self.refresh_icon_box.children = (img_w,)

        i = 0
        f = 0
        while self.started_scan:
            time.sleep(0.1)
            i += 1
            file = open(".img/refresh_" + str(i).zfill(2) + ".png", "rb")
            image = file.read()
            img_w .value = image
            if i == 11:
                i = -1
            f += 1
        
        # Ended scan, blank the resfresh image
        file = open(".img/tick.png", "rb")
        image = file.read()
        img_w .value = image

        if self.interrupted_scan:
            file = open(".img/close.png", "rb")
            image = file.read()
            img_w .value = image
        
    def clean_refresh_icon(self):
        file = open(".img/blank.png", "rb")
        image = file.read()
        img_w = widgets.Image(
            value=image,
            format='png',
            width=35,
            height=35,
        )
        
        self.refresh_icon_box.children = (img_w,)
        
    def export_image_thread(self):
        updating = True
        while True:
            if self.export:
                if updating:
                    if self.select_plot_option.value != 'Plot after ends with PyQt':
                        img = IPython.display.Image(filename=self.scan_names[-1] + ".png")
                        IPython.display.update_display(img, display_id='img')
                    
                    updating = False
            else:
                if not updating:
                    if self.select_plot_option.value != 'Plot after ends with PyQt':
                        IPython.display.update_display("", display_id='img')
                    
                    updating = True
                
            time.sleep(0.5)
            
    def load_image_file(self, filename):
        self.fig_box.children = []
        
        img = IPython.display.Image(filename=filename)
        IPython.display.update_display(img, display_id='img')

    def clear_image_file(self):
        IPython.display.update_display("", display_id='img')
    
    def display_start_button(self):
        display(self.select_plot_option,
                self.start_button, self.refresh_icon_box, self.fig_box, self.output)
        
        IPython.display.display((""), display_id='img')
        IPython.display.display((""), display_id='text')
        
        self.export_thread = threading.Thread(target=self.export_image_thread)
        self.export_thread.start()

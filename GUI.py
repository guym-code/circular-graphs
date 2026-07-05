#import CircularGraph

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk

import webbrowser

class CircularGraphGUI:

    def __init__(self):
        # Create the window
        self.root = tk.Tk()
        self.root.title('Circular Graph Plotter')
        self.root.geometry('770x520') # Window size
        self.root.grid_columnconfigure(0, weight=1)

        self.background_image = Image.open('circular_graph_bckg.jpeg').resize((770, 520))
        self.background_photo = ImageTk.PhotoImage(self.background_image)
        self.canvas = tk.Canvas(self.root, width=770, height=520, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.background_photo, anchor='nw')

        self.create_widgets()
        self.color_palette_path = None

        self.root.mainloop()

    def create_widgets(self):
        """Create all GUI widgets."""
        # Create Gui Title
        self.canvas.create_text(385, 45, text='Circular Graph Plotter', font=('Calibri Light', 20, 'bold'), fill='black')
        # title = tk.Label(self.root, text='Circular Graph Plotter', font=('Calibri Light', 20, 'bold'), bg=self.root['bg'])
        # title.grid(row=0, column=0, pady=20)

        # Create Data Subtitle
        self.canvas.create_text(20, 110, text='Data', anchor='nw', font=('Calibri Light', 14, 'bold'), fill='black')
        # self.data_label = tk.Label(self.root, text='Data', font=('Calibri Light', 14, 'bold'))
        # self.data_label.grid(row=1, column=0, sticky='w', padx=20, pady=(5, 2))

        # Create entry for conn mat path
        self.canvas.create_text(20, 155, text='Path to conn mat/Edges file:', anchor='nw', font=('Calibri', 11), fill='black')
        # self.mat_label = tk.Label(self.root, text='Path to conn mat/Edges file:')
        # self.mat_label.grid(row=2, column=0, sticky='w', padx=20, pady=2)
        self.mat_entry = tk.Entry(self.root, width=50)
        self.mat_entry.place(x=250, y=155)
        self.mat_browse_button = tk.Button(self.root, text='Browse...', command=self.browse_mat_file)
        self.mat_browse_button.place(x=600, y=150)
        
        self.file_type = tk.StringVar(value='')
        self.connmat_rb = tk.Radiobutton(self.root, text='Connectivity matrix', variable=self.file_type, value='matrix')
        self.connmat_rb.grid(row=3, column=0, sticky='w', padx=(198, 0), pady=2)
        self.edges_rb = tk.Radiobutton(self.root, text='Edge list', variable=self.file_type, value='edge_list')
        self.edges_rb.grid(row=3, column=0, sticky='w', padx=(360, 0), pady=2)

        # Create Options and entry for atlas
        atlas_1_options = ['Choose an Atlas', 'Multi-Modal Parcellation (MMP)', 'Schaefer 100', 'Schaefer 400', 'Schaefer 600', 'Schaefer 1000', 'Other']
        self.atlas_1_label = tk.Label(self.root, text='Choose Atlas or labels file:')
        self.atlas_1_label.grid(row=4, column=0, sticky='w', padx=20, pady=2)

        self.atlas_1_choice = ttk.Combobox(self.root, values=atlas_1_options, state='readonly', width=27)
        self.atlas_1_choice.grid(row=4, column=0, sticky='w', padx=(198, 0), pady=2)
        self.atlas_1_choice.current(0)

        self.other_1_entry = tk.Entry(self.root, width=45)
        self.other_1_entry.insert(0, 'Enter path here..')
        self.other_1_entry.config(fg='gray')
        self.other_1_entry.bind('<FocusIn>', lambda event: self.clear_placeholder(event, self.other_1_entry))
        self.other_1_entry.bind('<FocusOut>', lambda event: self.restore_placeholder(event, self.other_1_entry))

        self.atlas_1_choice.bind('<<ComboboxSelected>>', self.first_labels_change)

        # Create entry for secondary label
        atlas_2_options = ['Choose a file', 'Schaefer 100', 'Schaefer 400', 'Schaefer 600', 'Schaefer 1000', 'Other']
        self.atlas_2_label = tk.Label(self.root, text='Secondary label file (optional):')
        self.atlas_2_label.grid(row=5, column=0, sticky='w', padx=20, pady=2)

        self.atlas_2_choice = ttk.Combobox(self.root, values=atlas_2_options, state='readonly', width=27)
        self.atlas_2_choice.grid(row=5, column=0, sticky='w', padx=(198, 0), pady=2)
        self.atlas_2_choice.current(0)

        self.other_2_entry = tk.Entry(self.root, width=45)
        self.other_2_entry.insert(0, 'Enter path here..')
        self.other_2_entry.config(fg='gray')
        self.other_2_entry.bind('<FocusIn>', lambda event: self.clear_placeholder(event, self.other_2_entry))
        self.other_2_entry.bind('<FocusOut>', lambda event: self.restore_placeholder(event, self.other_2_entry))

        self.atlas_2_choice.bind('<<ComboboxSelected>>', self.secondary_labels_change)

        # Create Plot Subtitle
        self.plot_label = tk.Label(self.root, text='Plot', font=('Calibri Light', 14, 'bold'))
        self.plot_label.grid(row=6, column=0, sticky='w', padx=20, pady=(20, 2))

        # Create first level labeling
        self.labeling_label = tk.Label(self.root, text='Choose 1st level labeling:')
        self.labeling_label.grid(row=7, column=0, sticky='w', padx=20, pady=2)

        first_level_label_options = [False, True]
        self.labeling_choice = ttk.Combobox(self.root, values=first_level_label_options, state='readonly', width=10)
        self.labeling_choice.grid(row=7, column=0, sticky='w', padx=(198, 0), pady=2)

        self.labeling_choice.current(0)

        # Create secondary label method
        self.secondary_option_label = tk.Label(self.root, text='Choose secondary labeling:')
        self.secondary_option_label.grid(row=8, column=0, sticky='w', padx=20, pady=2)

        self.color_var = tk.BooleanVar()
        self.color_cb = tk.Checkbutton(self.root, text='Color', variable=self.color_var, command=lambda: self.update_secondary_options('color'))
        self.color_cb.grid(row=8, column=0, sticky='w', padx=(198, 0), pady=2)

        self.color_palette_button = tk.Button(self.root, text='Select Color palette', command=self.select_color_palette)

        self.grouping_var = tk.BooleanVar()
        self.grouping_cb = tk.Checkbutton(self.root, text='Grouping', variable=self.grouping_var, command=lambda: self.update_secondary_options('bracket'))
        self.grouping_cb.grid(row=8, column=0, sticky='w', padx=(270, 0), pady=2)

        self.none_var = tk.BooleanVar()
        self.none_cb = tk.Checkbutton(self.root, text='None', variable=self.none_var, command=lambda: self.update_secondary_options('none'))
        self.none_cb.grid(row=8, column=0, sticky='w', padx=(362, 0), pady=2)

        self.warning_label = tk.Label(self.root, text='', fg='red')
        self.warning_label.grid(row=5, column=0, sticky='w', padx=(250, 10), pady=(45,0))

        # Create edge color method
        self.edge_color_label = tk.Label(self.root, text='Edge color method:')
        self.edge_color_label.grid(row=9, column=0, sticky='w', padx=20, pady=2)

        edge_color_options = ['Uniform', 'PositiveNegative', 'Node', 'Nodes']

        self.edge_color_choice = ttk.Combobox(self.root, values=edge_color_options, state='readonly', width=20)
        self.edge_color_choice.grid(row=9, column=0, sticky='w', padx=(198, 0), pady=2)
        self.edge_color_choice.current(0)
        self.edge_help_button = tk.Button(self.root, text='?', width=2, command=self.show_edge_color_help)
        self.edge_help_button.grid(row=9, column=0, sticky='w', padx=(352, 0), pady=2)

        # Create threshold part
        threshold_options = ['Not thresholded', 'Weighted Average', 'Positive Negative Val', 'Positive Negative Percentile']
        self.threshold_label = tk.Label(self.root, text='Threshold method:')
        self.threshold_label.grid(row=10, column=0, sticky='w', padx=20, pady=2)
        self.threshold_choice = ttk.Combobox(self.root, values=threshold_options, state='readonly', width=28)
        self.threshold_choice.grid(row=10, column=0, sticky='w', padx=(198, 0), pady=2)
        self.threshold_choice.current(0)

        self.threshold_choice.bind('<<ComboboxSelected>>', self.update_threshold_entries)
        
        self.threshold_help_button = tk.Button(self.root, text='?', width=2, command=self.show_threshold_help)
        self.threshold_help_button.grid(row=10, column=0, sticky='w', padx=(400, 0), pady=2)

        self.threshold_label_1 = tk.Label(self.root)
        self.threshold_entry_1 = tk.Entry(self.root, width=10)

        self.threshold_label_2 = tk.Label(self.root)
        self.threshold_entry_2 = tk.Entry(self.root, width=10)

        # Create circular graph file attributes
        self.filename_label = tk.Label(self.root, text='Output filename:')
        self.filename_label.grid(row=11, column=0, sticky='w', padx=20, pady=2)

        self.filename_entry = tk.Entry(self.root, width=35)
        self.filename_entry.grid(row=11, column=0, sticky='w', padx=(198, 0), pady=2)

        self.fileformat_label = tk.Label(self.root, text='format:')
        self.fileformat_label.grid(row=11, column=0, sticky='w', padx=(480, 0), pady=2)

        file_formats = ['png', 'jpeg', 'svg', 'pdf']
        self.format_choice = ttk.Combobox(self.root, values=file_formats, state='readonly', width=8)
        self.format_choice.grid(row=11, column=0, sticky='w', padx=(550, 0), pady=2)
        self.format_choice.current(0)

        self.done_button = tk.Button(self.root, text='Done', command=self.plot_circular_graph)
        self.done_button.grid(row=12, column=0, pady=20)

    def check_secondary_input(self):
        if (self.color_var.get() or self.grouping_var.get()) and self.atlas_2_choice.get() == 'Choose a file':
            self.warning_label.config(text='Please choose a secondary label file.')
            return False

        self.warning_label.config(text='')
        return True

    def first_labels_change(self, event):
        if self.atlas_1_choice.get() == 'Other':
            self.other_1_entry.grid(row=4, column=0, sticky='w', padx=(400, 0), pady=2)
        else:
            self.other_1_entry.grid_remove()
        
            self.other_1_entry.grid_remove()

    def secondary_labels_change(self, event):
        if self.atlas_2_choice.get() == 'Other':
            self.other_2_entry.grid(row=5, column=0, sticky='w', padx=(400, 0), pady=2)
        else:
            self.other_2_entry.grid_remove()
        
        self.check_secondary_input()
    

    def clear_placeholder(self, event, other_entry):
        if other_entry.get() == 'Enter path here..':
            other_entry.delete(0, tk.END)
            other_entry.config(fg='black')

    def restore_placeholder(self, event, other_entry):
        if other_entry.get() == "":
            other_entry.insert(0, 'Enter path here..')
            other_entry.config(fg='gray')

    def update_secondary_options(self, clicked):
        if clicked == 'none' and self.none_var.get():
            self.color_var.set(False)
            self.grouping_var.set(False)
            self.color_palette_button.grid_remove()

        elif clicked in ('color', 'bracket'):
            if self.color_var.get():
                self.none_var.set(False)
                self.color_palette_button.grid(row=8, column=0, sticky='w', padx=(450, 0), pady=2)
            
            elif self.grouping_var.get():
                self.none_var.set(False)
                self.color_palette_button.grid_remove()

        
        self.check_secondary_input()
    
    def show_edge_color_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title('Edge Color Methods')
        help_window.geometry('350x250')

        tk.Label(help_window, text='Uniform', font=('Calibri', 10, 'bold')).pack(anchor='w', padx=10)
        tk.Label(help_window, text='All edges are displayed using the same color.', justify='left').pack(anchor='w', padx=20)

        tk.Label(help_window, text='PositiveNegative', font=('Calibri', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
        tk.Label(help_window, text='Positive edges are colored red and negative edges are \ncolored blue.', justify='left').pack(anchor='w', padx=20)

        tk.Label(help_window, text='Node', font=('Calibri', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
        tk.Label(help_window, text='Each edge is colored according to the color of the lower \nindexed node.', justify='left').pack(anchor='w', padx=20)

        tk.Label(help_window, text='Nodes', font=('Calibri', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
        tk.Label(help_window, text='Each edge is colored with a gradient between the colors of \nits two connected nodes.', justify='left').pack(anchor='w', padx=20)


    def show_threshold_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title('Thresholding Methods')
        help_window.geometry('350x350')

        tk.Label(help_window, text='Not thresholded', font=('Calibri', 10, 'bold')).pack(anchor='w', padx=10)
        tk.Label(help_window, text='Show all edges.', justify='left').pack(anchor='w', padx=20)

        tk.Label(help_window, text='Weighted Average', font=('Calibri', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
        tk.Label(help_window, text='Display only edges connected to nodes whose average \nabsolute edge weight is greater than the specified \nthreshold (exclusive). \n Range: 0–1.', justify='left').pack(anchor='w', padx=20)

        tk.Label(help_window, text='Positive Negative Val', font=('Calibri', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
        tk.Label(help_window, text='Display only edges whose weight is greater than the \nspecified positive threshold or less than the specified \nnegative threshold (exclusive). \nPositive range: 0–1. \nNegative range: –1–0.', justify='left').pack(anchor='w', padx=20)

        tk.Label(help_window, text='Positive Negative Percentile', font=('Calibri', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
        tk.Label(help_window, text='Display only edges whose weights fall within the selected \npercentile of the positive or negative edge-weight \ndistribution. \nRange: 0–100.', justify='left').pack(anchor='w', padx=20)

    def select_color_palette(self):
        self.color_window = tk.Toplevel(self.root)
        self.color_window.title('Color palette')
        self.color_window.geometry('480x100')

        tk.Label(self.color_window, text='Path to color palette CSV:').grid(row=0, column=0, sticky='w', padx=(10, 0), pady=2)

        self.color_palette_entry = tk.Entry(self.color_window, width=40)
        self.color_palette_entry.grid(row=0, column=0, sticky='w', padx=(160, 0), pady=2)

        tk.Button(self.color_window, text='Browse...', command=self.browse_color_palette).grid(row=0, column=0, sticky='w', padx=(410, 0), pady=2)
        tk.Button(self.color_window, text='Example File', command=self.open_example_csv).grid(row=1, column=0, sticky='w', padx=(210, 0), pady=2)
        tk.Button(self.color_window, text='Done', command=self.save_color_palette).grid(row=2, column=0, sticky='w', padx=(227, 0), pady=2)

    def browse_color_palette(self):
        filename = filedialog.askopenfilename(filetypes=[('CSV files', '*.csv')])

        if filename:
            self.color_palette_entry.delete(0, tk.END)
            self.color_palette_entry.insert(0, filename)
    
    def save_color_palette(self):
        self.color_palette_path = self.color_palette_entry.get().strip()
        self.color_window.destroy()
    
    def open_example_csv(self):
        webbrowser.open('https://github.com/guym-code/circular-graphs/blob/main/Color%20Palettes/yeo_7_network_colors.csv')

    def browse_mat_file(self):
        filename = filedialog.askopenfilename(title='Select connectivity matrix')
        if filename:
            self.mat_entry.delete(0, tk.END)
            self.mat_entry.insert(0, filename)

    def get_atlas(self, atlas_getter, other_getter):
        if atlas_getter not in ('Other', 'Choose an Atlas'):
            return atlas_getter
        elif atlas_getter == 'Other':
            return other_getter
        
        return None
    
    def get_second_label_presentations(self, color_var, grouping_var):
        if color_var and grouping_var:
            return 'ColorBracket'
        
        elif color_var:
            return 'Color'
        
        elif self.grouping_var:
            return 'Bracket'

        return 'False'

    def update_threshold_entries(self, event=None):

        self.threshold_label_1.grid_remove()
        self.threshold_entry_1.grid_remove()
        self.threshold_label_2.grid_remove()
        self.threshold_entry_2.grid_remove()

        method = self.threshold_choice.get()

        if method == 'Weighted Average':
            self.threshold_label_1.config(text='Weight [0,1]:')
            self.threshold_label_1.grid(row=10, column=0, sticky='w', padx=(430, 0))
            self.threshold_entry_1.grid(row=10, column=0, sticky='w', padx=(510, 0))

        elif method == 'Positive Negative Val':
            self.threshold_label_1.config(text='Positive [0, 1]:')
            self.threshold_label_1.grid(row=10, column=0, sticky='w', padx=(430, 0))
            self.threshold_entry_1.grid(row=10, column=0, sticky='w', padx=(510, 0))

            self.threshold_label_2.config(text='Negative [-1, 0]:')
            self.threshold_label_2.grid(row=10, column=0, sticky='w', padx=(570, 0))
            self.threshold_entry_2.grid(row=10, column=0, sticky='w', padx=(660, 0))
        
        elif method == 'Positive Negative Percentile':
            self.threshold_label_1.config(text='Positive [0, 100]:')
            self.threshold_label_1.grid(row=10, column=0, sticky='w', padx=(430, 0))
            self.threshold_entry_1.grid(row=10, column=0, sticky='w', padx=(520, 0))

            self.threshold_label_2.config(text='Negative [0, 100]:')
            self.threshold_label_2.grid(row=10, column=0, sticky='w', padx=(570, 0))
            self.threshold_entry_2.grid(row=10, column=0, sticky='w', padx=(665, 0))
            

    def plot_circular_graph(self):
        self.attributes = {
            'mat_path': self.mat_entry.get().strip(),
            'mat_type': self.file_type.get(),
            'show_first_labels': self.labeling_choice.get() == 'True',
            'show_second_labels': self.get_second_label_presentations(self.color_var.get(), self.grouping_var.get()),
            'color_palette': self.color_palette_path,
            'edge_color_method': self.edge_color_choice.get(),
            'output_file': f'{self.filename_entry.get().strip()}.{self.format_choice.get()}'
        }

        self.attributes['first_labels_file'] = self.get_atlas(self.atlas_1_choice.get(), self.other_1_entry.get().strip())
        self.attributes['secondary_labels_file'] = self.get_atlas(self.atlas_2_choice.get(), self.other_2_entry.get().strip())

        print(self.attributes)
        # cg_object = CircularGraph(
        #             mat_path=self.attributes['mat_path'],
        #             mat_type=self.attributes['mat_type'],
        #             labels=self.attributes['first_labels_file'],
        #             secondary_labels=self.attributes['secondary_labels_file'],
        #             color_palette=self.attributes['color_palette']
        #             )


if __name__ == '__main__':
    CircularGraphGUI()
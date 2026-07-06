# Imports
#import CircularGraph

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk

import webbrowser

class CircularGraphGUI:

    def __init__(self):
        # Init variables
        self.browse_button_txt = 'Browse'
        self.title_font = ('Calibri Light', 20, 'bold')
        self.subtitle_font = ('Calibri Light', 14, 'bold')
        self.body_font = ('Calibri Light', 10)
        self.txt_color = 'black'
        self.help_window_titles = ('Calibri Light', 10, 'bold')
        self.anchor = 'nw'
        self.combox_state = 'readonly'
        self.center_color = '#F6F7FC'
        self.side_color = '#EDF4FC'
        self.help_window_justify = 'left'

        # Create window
        self.root = tk.Tk()
        self.root.geometry('770x520') # Window size

        # Set the window title and icon
        self.root.title('Circular Graph Plotter')
        icon = tk.PhotoImage(file='brain_icon.png')
        self.root.iconphoto(True, icon)

        # Set background image
        self.background_image = Image.open('circular_graph_bckg.jpeg').resize((770, 520))
        self.background_image = ImageTk.PhotoImage(self.background_image)
        self.canvas = tk.Canvas(self.root, width=770, height=520, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.background_image, anchor=self.anchor)

        # Initialize optional color palette path, default is none
        self.color_palette_path = None

        self.create_widgets()

        # Open GUI
        self.root.mainloop()


    def create_widgets(self):
        """Create all GUI widgets."""
        # Create Gui Title
        self.canvas.create_text(385, 45, text='Circular Graph Plotter', font=self.title_font, fill=self.txt_color)

        # Create Data Subtitle
        self.canvas.create_text(20, 80, text='Data', anchor=self.anchor, font=self.subtitle_font, fill=self.txt_color)

        # Create connectivity matrix/edge list file input
        self.canvas.create_text(20, 120, text='Path to conn mat/Edges file:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        self.mat_entry = self.create_entry(50, 200, 120)
        self.mat_browse_button = self.create_button(self.browse_button_txt, self.browse_action, 530, 117, entry=self.mat_entry)
        
        # Create connectivity matrix file type options
        self.file_type = tk.StringVar(value='')
        self.connmat_rb = tk.Radiobutton(self.root, text='Connectivity matrix', variable=self.file_type, value='matrix', bg=self.center_color)
        self.connmat_rb.place(x=227, y=145)
        self.edges_rb = tk.Radiobutton(self.root, text='Edge list', variable=self.file_type, value='edge_list', bg=self.center_color)
        self.edges_rb.place(x=397, y=145)

        # Create Options and entry for atlas
        self.canvas.create_text(20, 170, text='Choose Atlas or labels file:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        atlas_1_options = ['Choose an Atlas', 'Multi-Modal Parcellation (MMP)', 'Schaefer 100', 'Schaefer 400', 'Schaefer 600', 'Schaefer 1000', 'Other']
        choice_change_args_first = ('first', 400, 172, 690, 165)
        self.atlas_1_choice, self.other_1_entry, self.other_1_browse_button = self.create_multi_options_other(atlas_1_options, 27, 200, 170, 45, 'Enter path here..', self.browse_action, self.clear_placeholder, self.restore_placeholder, self.choice_change, choice_change_args_first)

        # Create entry for secondary label
        self.canvas.create_text(20, 195, text='Secondary label file (optional):', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        atlas_2_options = ['Choose a file', 'Schaefer 100', 'Schaefer 400', 'Schaefer 600', 'Schaefer 1000', 'Other']
        choice_change_args_second = ('second', 400, 195, 690, 192)
        self.atlas_2_choice, self.other_2_entry, self.other_2_browse_button = self.create_multi_options_other(atlas_2_options, 27, 200, 195, 45, 'Enter path here..', self.browse_action, self.clear_placeholder, self.restore_placeholder, self.choice_change, choice_change_args_second)

        # Create Plot Subtitle
        self.canvas.create_text(20, 240, text='Plot Parameters', anchor=self.anchor, font=self.subtitle_font, fill=self.txt_color)

        # Create first level labeling
        self.canvas.create_text(20, 280, text='Choose 1st level labeling:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        first_level_label_options = [False, True]
        self.labeling_choice = self.create_combox(first_level_label_options, 10, 200, 278)

        # Create secondary label method
        self.canvas.create_text(20, 305, text='Choose secondary labeling:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        self.color_var, self.color_cb = self.create_checkbuton('Color', self.update_secondary_options, 195, 300)
        self.color_palette_button = tk.Button(self.root, text='Select Color palette', bg=self.center_color, command=self.select_color_palette)

        self.grouping_var, self.grouping_cb = self.create_checkbuton('Grouping', self.update_secondary_options, 260, 300)
        self.none_var, self.none_cb = self.create_checkbuton('None', self.update_secondary_options, 343, 301)

        self.warning_label = tk.Label(self.root, text='', fg='red', bg=self.side_color)
        self.warning_label.place(x=200, y=220)

        # Create edge color method
        self.canvas.create_text(20, 330, text='Edge color method:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)

        edge_color_options = ['Uniform', 'PositiveNegative', 'Node', 'Nodes']
        self.edge_color_choice = self.create_combox(edge_color_options, 20, 200, 327)
        self.edge_help_button = self.create_button('?', self.show_edge_color_help, 400, 323, 2)

        # Create threshold part
        self.canvas.create_text(20, 355, text='Threshold method:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)

        threshold_options = ['Not thresholded', 'Weighted Average', 'Positive Negative Val', 'Positive Negative Percentile']
        self.threshold_choice = self.create_combox(threshold_options, 28, 200, 352)
        self.threshold_choice.bind('<<ComboboxSelected>>', self.update_threshold_entries)
        self.threshold_help_button = self.create_button('?', self.show_threshold_help, 400, 352, 2)

        self.threshold_label_1 = tk.Label(self.root)
        self.threshold_entry_1 = tk.Entry(self.root, width=10)

        self.threshold_label_2 = tk.Label(self.root)
        self.threshold_entry_2 = tk.Entry(self.root, width=10)

        # Create circular graph file attributes
        self.canvas.create_text(20, 380, text='Output filename:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        self.filename_entry = self.create_entry(35, 200, 380)

        self.canvas.create_text(485, 382, text='format:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)

        file_formats = ['png', 'jpeg', 'svg', 'pdf']
        self.format_choice = self.create_combox(file_formats, 8, 570, 378)

        self.done_button = self.create_button('Done', self.plot_circular_graph, 370, 460)
    

    def create_entry(self, width, x, y):
        entry = tk.Entry(self.root, width=width)
        entry.place(x=x, y=y)

        return entry
    

    def create_button(self, txt, cmd, x, y, width = None, entry=None):
        button = tk.Button(self.root, text=txt, command=lambda: cmd(entry) if entry else cmd(), width=width)
        button.place(x=x, y=y)

        return button
    

    def create_combox(self, options, width, x, y):
        choice = ttk.Combobox(self.root, values=options, state=self.combox_state, width=width)
        choice.place(x=x, y=y)
        choice.current(0)

        return choice
    

    def create_checkbuton(self, txt, cmd, x, y):
        bool_var = tk.BooleanVar()
        cb = tk.Checkbutton(self.root, text=txt, variable=bool_var, bg=self.side_color, command=lambda: cmd(txt))
        cb.place(x=x, y=y)

        return bool_var, cb
    

    def create_multi_options_other(self, options, choice_width, x, y, entry_width, other_entry_txt, browse_func, clear, restore, label_change, label_change_args):
        choice_box = self.create_combox(options, choice_width, x, y)

        entry = tk.Entry(self.root, width=entry_width)
        entry.insert(0, other_entry_txt)
        entry.config(fg='gray')
        button = tk.Button(self.root, text=self.browse_button_txt, command=lambda: browse_func(entry))
        entry.bind('<FocusIn>', lambda event: clear(event, entry))
        entry.bind('<FocusOut>', lambda event: restore(event, entry))

        choice_box.bind('<<ComboboxSelected>>', lambda event: label_change(event, choice_box, entry, button, *label_change_args))

        return choice_box, entry, button


    def check_secondary_input(self):
        if (self.color_var.get() or self.grouping_var.get()) and self.atlas_2_choice.get() == 'Choose a file':
            self.warning_label.config(text='Please choose a secondary label file.')
            return False

        self.warning_label.config(text='')
        return True


    def choice_change(self, event, label, entry, button, level, x_entry, y_entry, x_button, y_button):
        if label.get() == 'Other':
            entry.place(x=x_entry, y=y_entry)
            button.place(x=x_button, y=y_button)
        
        else:
            entry.place_forget()
            button.place_forget()
        
        if level == 'second':
            self.check_secondary_input()
        

    def clear_placeholder(self, event, other_entry):
        if other_entry.get() == 'Enter path here..':
            other_entry.delete(0, tk.END)
            other_entry.config(fg=self.txt_color)


    def restore_placeholder(self, event, other_entry):
        if other_entry.get() == "":
            other_entry.insert(0, 'Enter path here..')
            other_entry.config(fg='gray')


    def update_secondary_options(self, clicked):
        if clicked == 'None' and self.none_var.get():
            self.color_var.set(False)
            self.grouping_var.set(False)
            self.color_palette_button.place_forget()

        elif clicked in ('Color', 'Grouping'):
            if self.color_var.get():
                self.none_var.set(False)
                self.color_palette_button.place(x=500, y=300)
            
            elif self.grouping_var.get():
                self.none_var.set(False)
                self.color_palette_button.place_forget()

        self.check_secondary_input()


    def create_help_window(self, title, size, background, labels_num, labels_help_dict):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry(size)
        window.configure(bg=background)
        padx_title = 10
        padx_body = 20
        pady = (10,0)

        for i in range(labels_num):
            tk.Label(window, text=labels_help_dict['title'][i], font=self.help_window_titles, bg=self.side_color).pack(anchor=self.anchor, padx=padx_title, pady=pady)
            tk.Label(window, text=labels_help_dict['body'][i], justify=self.help_window_justify, bg=self.side_color).pack(anchor=self.anchor, padx=padx_body)


    def show_edge_color_help(self):
        help_dict = {
            'title': ['Uniform', 'PositiveNegative', 'Node', 'Nodes'],
            'body': ['All edges are displayed using the same color.', 
                     'Positive edges are colored red and negative edges are \ncolored blue.',
                     'Each edge is colored according to the color of the lower \nindexed node.',
                     'Each edge is colored with a gradient between the colors of \nits two connected nodes.'
                     ]
        }

        self.create_help_window('Edge_color_help', '350x260', self.side_color, 4, help_dict)


    def show_threshold_help(self):
        help_dict = {
            'title': ['Not thresholded', 'Weighted Average', 'Positive Negative Val', 'Positive Negative Percentile'],
            'body': ['Show all edges.', 
                     'Display only edges connected to nodes whose average \nabsolute edge weight is greater than the specified \nthreshold (exclusive). \n Range: 0–1.',
                     'Display only edges whose weight is greater than the \nspecified positive threshold or less than the specified \nnegative threshold (exclusive). \nPositive range: 0–1. \nNegative range: –1–0.',
                     'Display only edges whose weights fall within the selected \npercentile of the positive or negative edge-weight \ndistribution. \nRange: 0–100.'
                     ]
        }

        self.create_help_window('Thresholding Methods', '350x370', self.side_color, 4, help_dict)


    def select_color_palette(self):
        self.color_window = tk.Toplevel(self.root)
        self.color_window.title('Color palette')
        self.color_window.geometry('480x100')
        self.color_window.configure(bg=self.side_color)

        tk.Label(self.color_window, text='Path to color palette CSV:', bg=self.side_color).grid(row=0, column=0, sticky=self.anchor, padx=(10, 0), pady=2)

        self.color_palette_entry = tk.Entry(self.color_window, width=40)
        self.color_palette_entry.grid(row=0, column=0, sticky=self.anchor, padx=(160, 0), pady=2)

        tk.Button(self.color_window, text=self.browse_button_txt, command=lambda: self.browse_action(self.color_palette_entry)).grid(row=0, column=0, sticky=self.anchor, padx=(410, 0), pady=2)
        tk.Button(self.color_window, text='Example File', command=self.open_example_csv).grid(row=1, column=0, sticky=self.anchor, padx=(210, 0), pady=2)
        tk.Button(self.color_window, text='Done', command=self.save_color_palette).grid(row=2, column=0, sticky=self.anchor, padx=(227, 0), pady=2)
    

    def save_color_palette(self):
        self.color_palette_path = self.color_palette_entry.get().strip()
        self.color_window.destroy()
    

    def open_example_csv(self):
        webbrowser.open('https://github.com/guym-code/circular-graphs/blob/main/Color%20Palettes/yeo_7_network_colors.csv')


    def browse_action(self, entry):
        filename = filedialog.askopenfilename()

        if filename:
            entry.delete(0, tk.END)
            entry.insert(0, filename)


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
            self.threshold_label_1.config(text='Weight [0,1]:', bg=self.side_color)
            self.threshold_label_1.place(x=440, y=352)
            self.threshold_entry_1.place(x=510, y=352)

        elif method == 'Positive Negative Val':
            self.threshold_label_1.config(text='Positive [0,1]:', bg=self.side_color)
            self.threshold_label_1.place(x=440, y=352)
            self.threshold_entry_1.place(x=520, y=352)

            self.threshold_label_2.config(text='Negative [-1,0]:', bg=self.side_color)
            self.threshold_label_2.place(x=590, y=352)
            self.threshold_entry_2.place(x=680, y=352)
        
        elif method == 'Positive Negative Percentile':
            self.threshold_label_1.config(text='Positive [0,100]:', bg=self.side_color)
            self.threshold_label_1.place(x=440, y=352)
            self.threshold_entry_1.place(x=530, y=352)

            self.threshold_label_2.config(text='Negative [0,100]:', bg=self.side_color)
            self.threshold_label_2.place(x=590, y=352)
            self.threshold_entry_2.place(x=690, y=352)
            

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
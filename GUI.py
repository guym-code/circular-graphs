# Imports
import CircularGraph as cg
from Plotting import defaults

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
from typing import Callable, Optional

import webbrowser


class CircularGraphGUI:

    def __init__(self):
        # Init variables
        self.browse_button_txt = 'Browse'

        self.title_font = ('Calibri Light', 20, 'bold')
        self.subtitle_font = ('Calibri Light', 14, 'bold')
        self.body_font = ('Calibri Light', 10)
        self.help_window_titles = ('Calibri Light', 10, 'bold')
        self.txt_color = 'black'
        
        self.anchor = 'nw'
        self.combox_state = 'readonly'
        self.help_window_justify = 'left'

        self.center_color = '#F6F7FC'
        self.side_color = '#EDF4FC'

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
        self.canvas.create_text(385, 45, text='NeuroCircle', font=self.title_font, fill=self.txt_color)

        # Create Data Subtitle
        self.canvas.create_text(20, 80, text='Data', anchor=self.anchor, font=self.subtitle_font, fill=self.txt_color)

        # Create connectivity matrix/edge list file input
        self.canvas.create_text(20, 120, text='Path to conn mat/Edges file:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        self.mat_entry = self.create_entry(50, 200, 120)
        self.mat_browse_button = self.create_button(self.browse_button_txt, self.browse_action, 530, 117, args=(self.mat_entry,))
        
        # Create connectivity matrix file type options
        self.file_type = tk.StringVar(value='')
        self.connmat_rb = tk.Radiobutton(self.root, text='Connectivity matrix', variable=self.file_type, value='matrix', bg=self.center_color)
        self.connmat_rb.place(x=227, y=145)
        self.edges_rb = tk.Radiobutton(self.root, text='Edge list', variable=self.file_type, value='edge_list', bg=self.center_color)
        self.edges_rb.place(x=397, y=145)

        # Create Options and entry for atlas
        self.canvas.create_text(20, 170, text='Choose atlas or labels file:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        atlas_1_options = ['Choose an atlas', 'Multi-Modal Parcellation (MMP)', 'Schaefer 100', 'Schaefer 400', 'Schaefer 600', 'Schaefer 1000', 'Other']
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

        help_dict = {
            'title': edge_color_options,
            'body': ['All edges are displayed using the same color.', 
                     'Positive edges are colored red and negative edges are \ncolored blue.',
                     'Each edge is colored according to the color of the lower \nindexed node.',
                     'Each edge is colored with a gradient between the colors of \nits two connected nodes.'
                     ]
        }
        edge_help_args = ('Edge_color_help', '350x260', self.side_color, 4, help_dict)
        self.edge_help_button = self.create_button('?', self.create_help_window, 400, 323, 2, edge_help_args)

        # Create threshold part
        self.canvas.create_text(20, 355, text='Threshold method:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)

        threshold_options = ['Not thresholded', 'Weighted Average', 'Positive Negative Val', 'Positive Negative Percentile']
        self.threshold_choice = self.create_combox(threshold_options, 28, 200, 352)
        self.threshold_choice.bind('<<ComboboxSelected>>', self.update_threshold_entries)
        
        help_dict = {
            'title': threshold_options,
            'body': ['Show all edges.', 
                     'Display only edges connected to nodes whose average \nabsolute edge weight is greater than the specified \nthreshold (exclusive). \n Range: 0–1.',
                     'Display only edges whose weight is greater than the \nspecified positive threshold or less than the specified \nnegative threshold (exclusive). \nPositive range: 0–1. \nNegative range: –1–0.',
                     'Display only edges whose weights fall within the selected \npercentile of the positive or negative edge-weight \ndistribution. \nRange: 0–100.'
                     ]
        }
        threshold_help_args = ('Thresholding Methods', '350x370', self.side_color, 4, help_dict)
        self.threshold_help_button = self.create_button('?', self.create_help_window, 400, 352, 2, threshold_help_args)

        self.threshold_label_1 = tk.Label(self.root)
        self.threshold_entry_1 = tk.Entry(self.root, width=10)

        self.threshold_label_2 = tk.Label(self.root)
        self.threshold_entry_2 = tk.Entry(self.root, width=10)

        # Create Radius part
        self.canvas.create_text(20, 380, text='Choose radius size [1,10]:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        self.radius = self.create_entry(10, 200, 380)

        # Create circular graph file attributes
        self.canvas.create_text(20, 405, text='Output filename:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)
        self.filename_entry = self.create_entry(35, 200, 405)

        self.canvas.create_text(485, 407, text='format:', anchor=self.anchor, font=self.body_font, fill=self.txt_color)

        file_formats = ['png', 'jpeg', 'svg', 'pdf']
        self.format_choice = self.create_combox(file_formats, 8, 570, 405)

        self.done_button = self.create_button('Done', self.plot_circular_graph, 370, 460)
    
    
    def create_entry(self, width: int, x: int, y: int) -> tk.Entry:
        """Create and place a text entry widget.

        Parameters
        ----------
        width : int
            Width of the entry widget.
        x : int
            Horizontal position.
        y : int
            Vertical position.

        Returns
        -------
        tk.Entry
            The created entry widget.
        """
        entry = tk.Entry(self.root, width=width)
        entry.place(x=x, y=y)

        return entry


    def create_button(
        self,
        txt: str,
        cmd: Callable,
        x: int,
        y: int,
        width: Optional[int] = None,
        args: Optional[tuple] = None
    ) -> tk.Button:
        """Create and place a button widget.

        Parameters
        ----------
        txt : str
            Text displayed on the button.
        cmd : Callable
            Function executed when the button is clicked.
        x : int
            Horizontal position of the button.
        y : int
            Vertical position of the button.
        width : int, optional
            Width of the button in characters. If ``None``, the default button width is used.
        args : tuple, optional
            Arguments passed to the command function. If ``None``, the command is
            called without arguments.

        Returns
        -------
        tk.Button
            The created button widget.
        """
        button = tk.Button(
            self.root,
            text=txt,
            command=lambda: cmd(*args) if args else cmd(),
            width=width
        )
        button.place(x=x, y=y)

        return button
    

    def create_combox(
            self, 
            options: list, 
            width: int, 
            x: int, 
            y: int
    ) -> ttk.Combobox:
        """Create and place a read-only combobox widget.

        Parameters
        ----------
        options : list
            List of values displayed in the combobox.
        width : int
            Width of the combobox in characters.
        x : int
            Horizontal position of the combobox.
        y : int
            Vertical position of the combobox.

        Returns
        -------
        ttk.Combobox
            The created combobox widget with the first option selected by default.
        """
        choice = ttk.Combobox(
            self.root, 
            values=options, 
            state=self.combox_state, 
            width=width
        )
        choice.place(x=x, y=y)
        choice.current(0)

        return choice
    
    
    def create_checkbuton(
            self, 
            txt: str, 
            cmd: Callable, 
            x: int, 
            y: int
    ) -> tuple[tk.BooleanVar, tk.Checkbutton]:
        """Create and place a checkbutton widget.

        Parameters
        ----------
        txt : str
            Text displayed next to the checkbutton.
        cmd : Callable
            Function executed when the checkbutton state changes.
        x : int
            Horizontal position of the checkbutton.
        y : int
            Vertical position of the checkbutton.

        Returns
        -------
        tuple
            A tuple containing:

            - tk.BooleanVar
                Variable associated with the checkbutton state.
            - tk.Checkbutton
                The created checkbutton widget.
        """
        bool_var = tk.BooleanVar()
        cb = tk.Checkbutton(
            self.root,
            text=txt,
            variable=bool_var, 
            bg=self.side_color, 
            command=lambda: cmd(txt)
        )
        cb.place(x=x, y=y)

        return bool_var, cb    
    
       
    def create_multi_options_other(
            self, 
            options: list, 
            choice_width: int, 
            x: int, 
            y: int, 
            entry_width: int, 
            other_entry_txt: str, 
            browse_func: Callable, 
            clear: Callable, 
            restore: Callable, 
            label_change: Callable, 
            label_change_args: tuple
    ) -> tuple[ttk.Combobox, tk.Entry, tk.Button]:
        """Create a combobox with an optional custom file entry.

        The combobox allows the user to select one of the predefined
        options. If the user selects ``Other``, an entry widget and a
        browse button are displayed, allowing a custom file to be selected.

        Parameters
        ----------
        options : list
            List of values displayed in the combobox.
        choice_width : int
            Width of the combobox in characters.
        x : int
            Horizontal position of the combobox.
        y : int
            Vertical position of the combobox.
        entry_width : int
            Width of the optional entry widget in characters.
        other_entry_txt : str
            Placeholder text displayed in the entry widget.
        browse_func : Callable
            Function executed when the browse button is clicked.
        clear : Callable
            Function executed when the entry widget gains focus to remove
            the placeholder text.
        restore : Callable
            Function executed when the entry widget loses focus to restore
            the placeholder text.
        label_change : Callable
            Function executed when the selected combobox option changes.
        label_change_args : tuple
            Additional arguments passed to ``label_change``.

        Returns
        -------
        tuple
            A tuple containing:

            - ttk.Combobox
                The created combobox widget.
            - tk.Entry
                The optional entry widget.
            - tk.Button
                The browse button associated with the entry widget.
        """
        choice_box = self.create_combox(options, choice_width, x, y)

        entry = tk.Entry(self.root, width=entry_width)
        entry.insert(0, other_entry_txt)
        entry.config(fg='gray')
        button = tk.Button(
            self.root, 
            text=self.browse_button_txt, 
            command=lambda: browse_func(entry)
        )
        entry.bind('<FocusIn>', lambda event: clear(event, entry))
        entry.bind('<FocusOut>', lambda event: restore(event, entry))

        choice_box.bind(
            '<<ComboboxSelected>>', 
            lambda event: label_change(
                event, 
                choice_box, 
                entry, 
                button, 
                *label_change_args
            )
        )

        return choice_box, entry, button
    

    def check_secondary_input(self) -> bool:
        """Validate the secondary labeling input.

        Checks whether a secondary label file has been selected when either
        node coloring or grouping is enabled. If the required file is
        missing, a warning message is displayed.

        Returns
        -------
        bool
            ``True`` if the current secondary labeling configuration is
            valid, otherwise ``False``.
        """
        if (
            self.color_var.get() or self.grouping_var.get()
        ) and self.atlas_2_choice.get() == 'Choose a file':
            self.warning_label.config(
                text='Please choose a secondary label file.'
            )
            return False

        self.warning_label.config(text='')
        return True

    
    def choice_change(
        self,
        event,
        label: ttk.Combobox,
        entry: tk.Entry,
        button: tk.Button,
        level: str,
        x_entry: int,
        y_entry: int,
        x_button: int,
        y_button: int
    ) -> None:
        """Update the GUI when the selected combobox option changes.

        Displays or hides the custom entry widget and its associated browse
        button depending on whether the user selects ``Other``. If the
        secondary label selection is modified, the secondary input is also
        validated.

        Parameters
        ----------
        event
            Combobox selection event.
        label : ttk.Combobox
            Combobox whose selected option has changed.
        entry : tk.Entry
            Entry widget used for specifying a custom file path.
        button : tk.Button
            Browse button associated with the entry widget.
        level : str
            Indicates whether the modified combobox corresponds to the
            first or second labeling level.
        x_entry : int
            Horizontal position of the entry widget.
        y_entry : int
            Vertical position of the entry widget.
        x_button : int
            Horizontal position of the browse button.
        y_button : int
            Vertical position of the browse button.

        Returns
        -------
        None
        """
        if label.get() == 'Other':
            entry.place(x=x_entry, y=y_entry)
            button.place(x=x_button, y=y_button)
        
        else:
            entry.place_forget()
            button.place_forget()
        
        if level == 'second':
            self.check_secondary_input()
      

    def clear_placeholder(
        self,
        event,
        other_entry: tk.Entry
    ) -> None:
        """Remove the placeholder text from an entry widget.

        Clears the placeholder text and restores the default text color
        when the entry widget gains focus.

        Parameters
        ----------
        event
            Entry focus event.
        other_entry : tk.Entry
            Entry widget containing the placeholder text.

        Returns
        -------
        None
        """
        if other_entry.get() == 'Enter path here..':
            other_entry.delete(0, tk.END)
            other_entry.config(fg=self.txt_color)


    def restore_placeholder(
        self,
        event,
        other_entry: tk.Entry
    ) -> None:
        """Restore the placeholder text in an entry widget.

        Restores the placeholder text and sets the text color to gray
        when the entry widget loses focus.

        Parameters
        ----------
        event
            Entry focus event.
        other_entry : tk.Entry
            Entry widget containing the placeholder text.

        Returns
        -------
        None
        """
        if other_entry.get() == '':
            other_entry.insert(0, 'Enter path here..')
            other_entry.config(fg='gray')


    def update_secondary_options(self, clicked: str) -> None:
        """Update secondary-label display options.

        Ensures that the secondary-label options behave consistently. If
        ``None`` is selected, node coloring and grouping are disabled. If
        ``Color`` is selected, the color palette button is displayed. If
        only ``Grouping`` is selected, the color palette button is hidden.

        Parameters
        ----------
        clicked : str
            Name of the checkbutton option that was clicked.

        Returns
        -------
        None
        """
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

    
    def create_help_window(
        self,
        title: str,
        size: str,
        background: str,
        labels_num: int,
        labels_help_dict: dict
    ) -> None:
        """Create and display a help window.

        Creates a pop-up window containing one or more help topics. Each
        topic consists of a bold title followed by a descriptive text.

        Parameters
        ----------
        title : str
            Title displayed in the help window.
        size : str
            Window dimensions in Tkinter geometry format (e.g., ``'350x260'``).
        background : str
            Background color of the help window.
        labels_num : int
            Number of help topics to display.
        labels_help_dict : dict
            Dictionary containing the help titles and descriptions. The
            dictionary must contain the keys ``'title'`` and ``'body'``,
            each mapped to a list of strings.

        Returns
        -------
        None
        """
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry(size)
        window.configure(bg=background)

        padx_title = 10
        padx_body = 20
        pady = (10, 0)

        for i in range(labels_num):
            tk.Label(
                window,
                text=labels_help_dict['title'][i],
                font=self.help_window_titles,
                bg=self.side_color
            ).pack(
                anchor=self.anchor,
                padx=padx_title,
                pady=pady
            )

            tk.Label(
                window,
                text=labels_help_dict['body'][i],
                justify=self.help_window_justify,
                bg=self.side_color
            ).pack(
                anchor=self.anchor,
                padx=padx_body
            )

    def select_color_palette(self) -> None:
        """Create a window for selecting a color palette.

        Opens a dialog that allows the user to specify a CSV file
        containing a custom color palette. The dialog also provides access
        to an example color palette file and allows the selected file to be
        saved.

        Returns
        -------
        None
        """
        self.color_window = tk.Toplevel(self.root)
        self.color_window.title('Color palette')
        self.color_window.geometry('480x100')
        self.color_window.configure(bg=self.side_color)

        tk.Label(
            self.color_window,
            text='Path to color palette CSV:',
            bg=self.side_color
        ).grid(
            row=0,
            column=0,
            sticky=self.anchor,
            padx=(10, 0),
            pady=2
        )

        self.color_palette_entry = tk.Entry(
            self.color_window,
            width=40
        )
        self.color_palette_entry.grid(
            row=0,
            column=0,
            sticky=self.anchor,
            padx=(160, 0),
            pady=2
        )

        tk.Button(
            self.color_window,
            text=self.browse_button_txt,
            command=lambda: self.browse_action(self.color_palette_entry)
        ).grid(
            row=0,
            column=0,
            sticky=self.anchor,
            padx=(410, 0),
            pady=2
        )

        tk.Button(
            self.color_window,
            text='Example File',
            command=self.open_example_csv
        ).grid(
            row=1,
            column=0,
            sticky=self.anchor,
            padx=(210, 0),
            pady=2
        )

        tk.Button(
            self.color_window,
            text='Done',
            command=self.save_color_palette
        ).grid(
            row=2,
            column=0,
            sticky=self.anchor,
            padx=(227, 0),
            pady=2
        )
    

    def save_color_palette(self):
        """Save the selected color palette path and close the dialog.

        Retrieves the file path entered in the color palette selection
        window, stores it, and closes the dialog.

        Returns
        -------
        None
        """
        self.color_palette_path = self.color_palette_entry.get().strip()
        self.color_window.destroy()
    

    def open_example_csv(self) -> None:
        """Open an example color palette file.

        Opens the default web browser and navigates to an example color
        palette CSV file hosted in the project's GitHub repository.

        Returns
        -------
        None
        """
        webbrowser.open(
            'https://github.com/guym-code/circular-graphs/blob/main/'
            'Color%20Palettes/yeo_7_network_colors.csv'
        )



    def browse_action(
        self,
        entry: tk.Entry
    ) -> None:
        """Open a file browser and update an entry widget.

        Opens a file selection dialog. If the user selects a file, its path
        is inserted into the specified entry widget.

        Parameters
        ----------
        entry : tk.Entry
            Entry widget that receives the selected file path.

        Returns
        -------
        None
        """
        filename = filedialog.askopenfilename()

        if filename:
            entry.delete(0, tk.END)
            entry.insert(0, filename)


    def get_atlas(self, atlas_getter, other_getter):
        if atlas_getter not in ('Other', 'Choose an atlas', 'Choose a file'):
            return atlas_getter
        elif atlas_getter == 'Other':
            return other_getter
        
        return None
    
    def get_atlas(
        self,
        atlas_getter: str,
        other_getter: str
    ) -> Optional[str]:
        """Return the selected atlas or custom labels file.

        Returns the selected predefined atlas name. If the user selected
        ``Other``, the path entered by the user is returned instead. If no
        valid selection has been made, ``None`` is returned.

        Parameters
        ----------
        atlas_getter : str
            Selected atlas option from the combobox.
        other_getter : str
            Path entered for a custom atlas or labels file.

        Returns
        -------
        Optional[str]
            Selected atlas name, custom file path, or ``None`` if no valid
            selection was made.
        """
        if atlas_getter not in ('Other', 'Choose an atlas', 'Choose a file'):
            return atlas_getter

        elif atlas_getter == 'Other':
            return other_getter

        return None
    
    

    def get_second_label_presentations(
        self,
        color_var: bool,
        grouping_var: bool
    ) -> str:
        """Return the selected secondary labeling presentation.

        Determines how secondary labels should be displayed based on the
        selected GUI options.

        Parameters
        ----------
        color_var : bool
            Indicates whether node coloring is enabled.
        grouping_var : bool
            Indicates whether group brackets are enabled.

        Returns
        -------
        str
            The selected secondary labeling presentation. Returns
            ``'Bracket'`` if grouping is enabled, ``'Color'`` if node
            coloring is enabled, or the default presentation defined by
            ``defaults.SEC_LABEL`` otherwise.
        """
        if grouping_var:
            return 'Bracket'

        elif color_var:
            return 'Color'

        return defaults.SEC_LABEL


    def change_threshold_entry_method(
        self,
        label: tk.Label,
        entry: tk.Entry,
        txt: str,
        label_x: int,
        label_y: int,
        entry_x: int,
        entry_y: int
    ) -> None:
        """Update the threshold label and entry widget.

        Configures the label text and background color, then positions the
        label and its corresponding entry widget according to the specified
        coordinates.

        Parameters
        ----------
        label : tk.Label
            Label widget associated with the threshold entry.
        entry : tk.Entry
            Entry widget for the threshold value.
        txt : str
            Text displayed on the label.
        label_x : int
            Horizontal position of the label.
        label_y : int
            Vertical position of the label.
        entry_x : int
            Horizontal position of the entry widget.
        entry_y : int
            Vertical position of the entry widget.

        Returns
        -------
        None
        """
        label.config(text=txt, bg=self.side_color)
        label.place(x=label_x, y=label_y)
        entry.place(x=entry_x, y=entry_y)


    def update_threshold_entries(self, event) -> None:
        """Update the threshold input fields.

        Displays the appropriate threshold labels and entry widgets
        according to the selected thresholding method.

        Parameters
        ----------
        event
            Combobox selection event.

        Returns
        -------
        None
        """
        method = self.threshold_choice.get()

        if method == 'Weighted Average':
            self.change_threshold_entry_method(
                self.threshold_label_1,
                self.threshold_entry_1,
                'Weight [0,1]:',
                440,
                352,
                510,
                352
            )
            self.threshold_label_2.place_forget()
            self.threshold_entry_2.place_forget()

        elif method == 'Positive Negative Val':
            self.change_threshold_entry_method(
                self.threshold_label_1,
                self.threshold_entry_1,
                'Positive [0,1]:',
                440,
                352,
                520,
                352
            )
            self.change_threshold_entry_method(
                self.threshold_label_2,
                self.threshold_entry_2,
                'Negative [-1,0]:',
                590,
                352,
                680,
                352
            )

        elif method == 'Positive Negative Percentile':
            self.change_threshold_entry_method(
                self.threshold_label_1,
                self.threshold_entry_1,
                'Positive [0,100]:',
                440,
                352,
                530,
                352
            )
            self.change_threshold_entry_method(
                self.threshold_label_2,
                self.threshold_entry_2,
                'Negative [0,100]:',
                590,
                352,
                690,
                352
            )

        else:
            self.threshold_label_1.place_forget()
            self.threshold_entry_1.place_forget()
            self.threshold_label_2.place_forget()
            self.threshold_entry_2.place_forget()

    
    def get_threshold(self):
        method = self.threshold_choice.get()
        params = None

        if method == 'Weighted Average':
            params =  {
                'method': 'weighted_average',
                'value': float(self.threshold_entry_1.get())
            }

        elif method == 'Positive Negative Val':
            params = {
                'method': 'positive_negative_value',
                'positive_value': float(self.threshold_entry_1.get()),
                'negative_value': float(self.threshold_entry_2.get())
            }

        elif method == 'Positive Negative Percentile':
            params = {
                'method': 'positive_negative_percentile_value',
                'value_positive': float(self.threshold_entry_1.get()),
                'value_negative': float(self.threshold_entry_2.get())
            }
        
        return params
            

    def plot_circular_graph(self):
        self.attributes = {
            'mat_path': self.mat_entry.get().strip(),
            'mat_type': self.file_type.get(),
            'show_first_labels': self.labeling_choice.get() == 'True',
            'show_second_labels': self.get_second_label_presentations(self.color_var.get(), self.grouping_var.get()),
            'color_palette': self.color_palette_path,
            'edge_color_method': self.edge_color_choice.get(),
            'radius': float(self.radius.get()),
            'output_file': f'{self.filename_entry.get().strip()}.{self.format_choice.get()}' if self.filename_entry.get().strip() is not None else f'{defaults.SAVE_NAME}.{self.format_choice.get()}',
            'output_format': self.format_choice.get()
        }

        self.attributes['first_labels_file'] = self.get_atlas(self.atlas_1_choice.get(), self.other_1_entry.get().strip())
        self.attributes['secondary_labels_file'] = self.get_atlas(self.atlas_2_choice.get(), self.other_2_entry.get().strip())

        cg_object = cg.CircularGraph(
                    mat_path=self.attributes['mat_path'],
                    mat_type=self.attributes['mat_type'],
                    labels=self.attributes['first_labels_file'],
                    secondary_labels=self.attributes['secondary_labels_file'],
                    color_palette=self.attributes['color_palette']
                    )

        threshold_params = self.get_threshold()
        if threshold_params:
            cg_object.apply_threshold(**threshold_params)

        cg_object.plot(label=self.attributes['show_first_labels'],
                       sec_label=self.attributes['show_second_labels'],
                       edge_color_method=self.attributes['edge_color_method'],
                       radius=self.attributes['radius']
        )

        cg_object.show()

        cg_object.savegraph(fname=self.attributes['output_file'],
                            format=self.attributes['output_format']
        )


if __name__ == '__main__':
    CircularGraphGUI()
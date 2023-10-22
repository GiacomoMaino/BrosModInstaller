# Credits: https://ttkbootstrap.readthedocs.io/en/version-0.5/gallery/collapsing_frame.html

import ttkbootstrap as ttk
from pathlib import Path
import tkinter

class CollapsingFrame(ttk.Frame):
    """
    A collapsible frame widget that opens and closes with a button click.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.cumulative_rows = 0
        p = Path(__file__).parent

    def add(self, child, title="", style='primary.TButton', **kwargs):
        """Add a child to the collapsible frame

        :param ttk.Frame child: the child frame to add to the widget
        :param str title: the title appearing on the collapsible section header
        :param str style: the ttk style to apply to the collapsible section header
        """
        if child.winfo_class() != 'TFrame':  # must be a frame
            return
        style_color = style.split('.')[0]
        frm = ttk.Frame(self, style=f'{style_color}.TFrame')
        frm.grid(row=self.cumulative_rows, column=0, sticky='ew')

        # header title
        lbl = ttk.Label(frm, text=title, style="inverse-"+style_color, font=("Arial", 25))
        if kwargs.get('textvariable'):
            lbl.configure(textvariable=kwargs.get('textvariable'))
        lbl.pack(side='left', fill='both', padx=10, pady=5)

        # header toggle button
        btn = ttk.Button(frm, text="v", style=style, command=lambda c=child: self._toggle_open_close(child))
        btn.pack(side='right')

        # assign toggle button to child so that it's accesible when toggling (need to change image)
        child.btn = btn
        child.grid(row=self.cumulative_rows + 1, column=0, sticky='news')

        # increment the row assignment
        self.cumulative_rows += 2

    def _toggle_open_close(self, child):
        """
        Open or close the section and change the toggle button image accordingly

        :param ttk.Frame child: the child element to add or remove from grid manager
        """
        if child.winfo_viewable():
            child.grid_remove()
            child.btn.configure(text=">")
        else:
            child.grid()
            child.btn.configure(text="v")
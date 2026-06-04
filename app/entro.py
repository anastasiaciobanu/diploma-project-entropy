import csv
import json
import math
import pathlib
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from parser import load_file, load_folder
from pipeline import (
    analyze,
    autocorrelation,
    bitstream,
    clean,
    distribution,
    entropy_over_time,
    fft_spectrum,
    mutual_information_by_lag,
)

# MAIN APPLICATION (entro.py)
#
# contains only the GUI of the application
#
# USAGE: terminal only, requires venv (standalone executable available in the project root)


# THEME
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

FONT = "DejaVu Sans Mono"

C = {
    "bg": "#080A0C",
    "panel": "#11161A",
    "card": "#1C242A",
    "card2": "#232D34",
    "accent": "#00FF99",
    "accent2": "#00C878",
    "text": "#F4F7F8",
    "muted": "#C9D2D8",
    "muted2": "#A8B4BC",
    "line": "#31404A",
    "button": "#10261D",
    "button_hover": "#173D2D",
    "danger": "#FF5C7A",
    "warn": "#FFD166",
}


# formats metric values for display without changing the computed results
def format_value(value):
    if value is None:
        return "N/A"

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        if math.isnan(value):
            return "N/A"

        if value != 0 and abs(value) < 1e-6:
            return f"{value:.6e}"

        if abs(value) > 10000:
            return f"{value:,.4f}"

        return f"{value:.8g}"

    return str(value)


# GUI
class EntroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("entro(py)")
        self.geometry("1360x850")
        self.minsize(1160, 740)
        self.configure(fg_color=C["bg"])

        self.data = {}
        self.results = {}
        self.active_dataset = None
        self.source = "no data loaded"
        self.page = "Overview"

        self.compare_a = None
        self.compare_b = None
        self.compare_a_name = "A"
        self.compare_b_name = "B"

        self.plot_kind = tk.StringVar(value="Distribution")
        self.compare_kind = tk.StringVar(value="Distribution")

        self.f_title = ctk.CTkFont(family=FONT, size=30, weight="bold")
        self.f_big = ctk.CTkFont(family=FONT, size=22, weight="bold")
        self.f_nav = ctk.CTkFont(family=FONT, size=17, weight="bold")
        self.f = ctk.CTkFont(family=FONT, size=17)
        self.f_bold = ctk.CTkFont(family=FONT, size=18, weight="bold")
        self.f_value = ctk.CTkFont(family=FONT, size=20, weight="bold")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_header()
        self.build_nav()

        self.content = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=18)
        self.content.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.show("Overview")

    # LAYOUT
    def build_header(self):
        header = ctk.CTkFrame(self, fg_color=C["bg"], height=70, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            header,
            text="entro(py)",
            font=self.f_title,
            text_color=C["accent"],
        ).grid(row=0, column=0, padx=(18, 14), pady=15, sticky="w")

        ctk.CTkLabel(
            header,
            text="stochastic analysis tool",
            font=self.f,
            text_color=C["muted"],
        ).grid(row=0, column=1, padx=(0, 18), pady=15, sticky="w")

        self.source_label = ctk.CTkLabel(
            header,
            text="[ no data loaded ]",
            font=self.f_bold,
            text_color=C["accent"],
        )
        self.source_label.grid(row=0, column=2, padx=12, pady=15, sticky="e")

        self.main_button(header, "[ load file ]", self.pick_file).grid(
            row=0,
            column=3,
            padx=8,
            pady=14,
        )

        self.main_button(header, "[ load folder ]", self.pick_folder).grid(
            row=0,
            column=4,
            padx=(8, 18),
            pady=14,
        )

    def build_nav(self):
        nav_frame = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=16, height=68)
        nav_frame.grid(row=1, column=0, padx=18, pady=(4, 14), sticky="ew")
        nav_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.nav_buttons = {}

        pages = ["Overview", "Analysis", "Visualizations", "Compare", "Export"]

        for index, page in enumerate(pages):
            button = ctk.CTkButton(
                nav_frame,
                text=page,
                font=self.f_nav,
                height=48,
                corner_radius=13,
                fg_color=C["card"],
                hover_color=C["button_hover"],
                text_color=C["text"],
                border_width=1,
                border_color=C["line"],
                command=lambda name=page: self.show(name),
            )
            button.grid(row=0, column=index, padx=8, pady=10, sticky="ew")
            self.nav_buttons[page] = button

    def main_button(self, parent, text, command):
        return ctk.CTkButton(
            parent,
            text=text,
            font=self.f_bold,
            height=42,
            fg_color=C["button"],
            hover_color=C["button_hover"],
            border_color=C["accent"],
            border_width=2,
            text_color=C["text"],
            command=command,
        )

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show(self, page):
        self.page = page

        for name, button in self.nav_buttons.items():
            is_active = name == page

            button.configure(
                fg_color=C["accent2"] if is_active else C["card"],
                text_color="#06100B" if is_active else C["text"],
                border_width=2 if is_active else 1,
                border_color=C["accent"] if is_active else C["line"],
            )

        self.clear_content()

        if page == "Overview":
            self.page_overview()
        elif page == "Analysis":
            self.page_analysis()
        elif page == "Visualizations":
            self.page_visualizations()
        elif page == "Compare":
            self.page_compare()
        elif page == "Export":
            self.page_export()

    # UI HELPERS
    def scroll_frame(self):
        frame = ctk.CTkScrollableFrame(
            self.content,
            fg_color=C["panel"],
            corner_radius=18,
            scrollbar_button_color=C["accent2"],
            scrollbar_button_hover_color=C["accent"],
        )
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        return frame

    def no_data_message(self, parent):
        card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=16)
        card.grid(row=0, column=0, padx=22, pady=22, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="No data loaded",
            font=self.f_big,
            text_color=C["accent"],
        ).grid(row=0, column=0, padx=22, pady=(22, 8), sticky="w")

        ctk.CTkLabel(
            card,
            text=(
                "Load a file or a folder to start the analysis. "
                "The application will process the data locally and switch to Overview."
            ),
            font=self.f,
            text_color=C["text"],
            wraplength=1050,
            justify="left",
        ).grid(row=1, column=0, padx=22, pady=(0, 22), sticky="w")

    def section(self, parent, row, title):
        ctk.CTkLabel(
            parent,
            text=f"— {title.upper()} —",
            font=self.f_bold,
            text_color=C["accent"],
            anchor="w",
        ).grid(row=row, column=0, padx=18, pady=(22, 10), sticky="ew")

        return row + 1

    def text_card(self, parent, row, title, body, color=None):
        card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=14)
        card.grid(row=row, column=0, padx=18, pady=9, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=self.f_big,
            text_color=color or C["accent"],
            anchor="w",
        ).grid(row=0, column=0, padx=18, pady=(16, 6), sticky="ew")

        ctk.CTkLabel(
            card,
            text=body,
            font=self.f,
            text_color=C["text"],
            wraplength=1120,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, padx=18, pady=(0, 18), sticky="ew")

        return row + 1

    def result_row(self, parent, row, label, value, accent=False):
        card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=12)
        card.grid(row=row, column=0, padx=18, pady=5, sticky="ew")
        card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            card,
            text=label,
            font=self.f_bold,
            text_color=C["text"] if accent else C["muted"],
            anchor="w",
        ).grid(row=0, column=0, padx=18, pady=13, sticky="w")

        ctk.CTkLabel(
            card,
            text=format_value(value),
            font=self.f_value,
            text_color=C["accent"] if accent else C["text"],
            anchor="e",
        ).grid(row=0, column=1, padx=18, pady=13, sticky="e")

        return row + 1

    # LOAD DATA
    def pick_file(self):
        path = filedialog.askopenfilename(
            title="Load file",
            filetypes=[
                ("Data files", "*.jsonl *.json *.txt *.csv *.bin *.raw *.dat *.log"),
                ("All files", "*.*"),
            ],
        )

        if not path:
            return

        values = load_file(path)

        if not values:
            messagebox.showerror(
                "No valid data",
                "The selected file does not contain valid values.",
            )
            return

        self.data = {"file": values}
        self.active_dataset = "file"
        self.source = f"file: {pathlib.Path(path).name}"

        self.refresh()

    def pick_folder(self):
        folder = filedialog.askdirectory(title="Load folder")

        if not folder:
            return

        data = load_folder(folder)

        if not data:
            messagebox.showerror(
                "No valid data",
                "The selected folder does not contain valid data files.",
            )
            return

        self.data = data
        self.active_dataset = list(data.keys())[0]
        self.source = f"folder: {pathlib.Path(folder).name}"

        self.refresh()

    def refresh(self):
        self.results = {}

        for name, values in self.data.items():
            self.results[name] = analyze(values)

        self.source_label.configure(text=f"[ {self.source} ]")

        self.show("Overview")

    def condition_selector(self, parent, row):
        if not self.data:
            return row

        box = ctk.CTkFrame(parent, fg_color=C["panel"], corner_radius=12)
        box.grid(row=row, column=0, padx=18, pady=(8, 6), sticky="ew")

        ctk.CTkLabel(
            box,
            text="Dataset:",
            font=self.f_bold,
            text_color=C["muted"],
        ).pack(side="left", padx=(0, 12))

        for name in self.data:
            is_active = name == self.active_dataset

            ctk.CTkButton(
                box,
                text=name.upper(),
                font=self.f_bold,
                height=38,
                width=130,
                fg_color=C["accent2"] if is_active else C["button"],
                hover_color=C["button_hover"],
                text_color="#06100B" if is_active else C["text"],
                border_color=C["accent"],
                border_width=2 if is_active else 1,
                command=lambda dataset=name: self.change_condition(dataset),
            ).pack(side="left", padx=6)

        return row + 1

    def change_condition(self, name):
        self.active_dataset = name
        self.show(self.page)

    # PAGES
    def page_overview(self):
        frame = self.scroll_frame()

        if not self.data:
            self.no_data_message(frame)
            return

        row = self.section(frame, 0, "Overview")

        row = self.text_card(
            frame,
            row,
            "Loaded data",
            (
                "The dataset was processed locally. This page gives a readable "
                "first interpretation before the exact values are inspected in Analysis."
            ),
        )

        for name, values in self.data.items():
            metrics = self.results[name]

            entropy_value = metrics["Shannon entropy"]
            chi_p = metrics["Chi-square p-value"]
            runs_p = metrics["Runs test p-value"]
            max_autocorr = metrics["Max autocorr lag 1-50"]

            if entropy_value >= 7.8:
                color = C["accent"]
            elif entropy_value >= 7.0:
                color = C["warn"]
            else:
                color = C["danger"]

            uniformity = "measurable deviation detected" if chi_p < 0.05 else "no strong deviation detected"
            temporal = "visible signals should be inspected" if runs_p < 0.05 or max_autocorr > 0.05 else "limited signals detected"

            body = (
                f"Samples processed: {metrics['Samples']:,}\n"
                f"Shannon entropy: {entropy_value:.6f} bits.\n"
                f"Uniformity: {uniformity}.\n"
                f"Temporal structure: {temporal}.\n\n"
                "This is an exploratory interpretation, not a cryptographic certification."
            )

            row = self.text_card(frame, row, name.upper(), body, color)

    def page_analysis(self):
        frame = self.scroll_frame()

        if not self.data:
            self.no_data_message(frame)
            return

        row = self.condition_selector(frame, 0)
        metrics = self.results[self.active_dataset]

        groups = {
            "Dataset": [
                "Samples",
                "Min",
                "Max",
                "Mean",
                "Standard deviation",
            ],
            "Entropy and complexity": [
                "Shannon entropy",
                "Permutation entropy",
            ],
            "Uniformity": [
                "Chi-square statistic",
                "Chi-square p-value",
                "Cramér's V",
            ],
            "Independence / temporal structure": [
                "Runs test z-stat",
                "Runs test p-value",
                "Serial correlation",
                "Max autocorr lag 1-50",
                "Mean mutual information",
            ],
        }

        accent_keys = {
            "Samples",
            "Shannon entropy",
            "Cramér's V",
            "Max autocorr lag 1-50",
            "Mean mutual information",
        }

        for title, keys in groups.items():
            row = self.section(frame, row, title)

            for key in keys:
                row = self.result_row(
                    frame,
                    row,
                    key,
                    metrics[key],
                    accent=key in accent_keys,
                )

    def page_visualizations(self):
        frame = ctk.CTkFrame(self.content, fg_color=C["panel"], corner_radius=18)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        if not self.data:
            self.no_data_message(frame)
            return

        top = ctk.CTkFrame(frame, fg_color=C["panel"], corner_radius=12)
        top.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        top.grid_columnconfigure(20, weight=1)

        ctk.CTkLabel(
            top,
            text="Dataset:",
            font=self.f_bold,
            text_color=C["muted"],
        ).grid(row=0, column=0, padx=(0, 10))

        for index, name in enumerate(self.data, start=1):
            is_active = name == self.active_dataset

            ctk.CTkButton(
                top,
                text=name.upper(),
                font=self.f_bold,
                height=38,
                width=130,
                fg_color=C["accent2"] if is_active else C["button"],
                hover_color=C["button_hover"],
                text_color="#06100B" if is_active else C["text"],
                border_color=C["accent"],
                border_width=2 if is_active else 1,
                command=lambda dataset=name: self.change_condition(dataset),
            ).grid(row=0, column=index, padx=5, pady=8)

        ctk.CTkOptionMenu(
            top,
            values=[
                "Distribution",
                "Autocorrelation",
                "FFT Spectrum",
                "Entropy Over Time",
                "Raw Sequence",
                "Mutual Information",
            ],
            variable=self.plot_kind,
            font=self.f_bold,
            dropdown_font=self.f,
            height=40,
            fg_color=C["button"],
            button_color=C["accent2"],
            button_hover_color=C["accent"],
            command=lambda _: self.draw_plot(),
        ).grid(row=0, column=20, padx=(16, 4), pady=8, sticky="e")

        self.plot_box = ctk.CTkFrame(frame, fg_color=C["card"], corner_radius=16)
        self.plot_box.grid(row=1, column=0, padx=16, pady=(8, 16), sticky="nsew")
        self.plot_box.grid_columnconfigure(0, weight=1)
        self.plot_box.grid_rowconfigure(0, weight=1)

        self.draw_plot()

    def page_compare(self):
        frame = ctk.CTkFrame(self.content, fg_color=C["panel"], corner_radius=18)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(frame, fg_color=C["panel"], corner_radius=12)
        top.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        top.grid_columnconfigure(9, weight=1)

        self.main_button(top, "[ load file A ]", lambda: self.pick_compare("A")).grid(
            row=0,
            column=0,
            padx=8,
            pady=8,
        )

        self.main_button(top, "[ load file B ]", lambda: self.pick_compare("B")).grid(
            row=0,
            column=1,
            padx=8,
            pady=8,
        )

        ctk.CTkOptionMenu(
            top,
            values=[
                "Distribution",
                "Autocorrelation",
                "FFT Spectrum",
                "Entropy Over Time",
                "Raw Sequence",
            ],
            variable=self.compare_kind,
            font=self.f_bold,
            dropdown_font=self.f,
            height=40,
            fg_color=C["button"],
            button_color=C["accent2"],
            command=lambda _: self.draw_compare(),
        ).grid(row=0, column=9, padx=8, pady=8, sticky="e")

        self.compare_info = ctk.CTkFrame(frame, fg_color=C["card"], corner_radius=16)
        self.compare_info.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        self.compare_info.grid_columnconfigure((0, 1), weight=1)

        self.compare_box = ctk.CTkFrame(frame, fg_color=C["card"], corner_radius=16)
        self.compare_box.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="nsew")
        self.compare_box.grid_columnconfigure(0, weight=1)
        self.compare_box.grid_rowconfigure(0, weight=1)

        self.draw_compare()

    def page_export(self):
        frame = self.scroll_frame()

        if not self.data:
            self.no_data_message(frame)
            return

        row = self.section(frame, 0, "Export")

        row = self.text_card(
            frame,
            row,
            "Export current analysis",
            (
                "Export saves analysis results without modifying the original files. "
                "The generated files can be used in reports, documentation or later verification."
            ),
        )

        box = ctk.CTkFrame(frame, fg_color=C["card"], corner_radius=16)
        box.grid(row=row, column=0, padx=18, pady=12, sticky="ew")
        box.grid_columnconfigure((0, 1, 2, 3), weight=1)

        actions = [
            ("JSON report", self.export_json),
            ("CSV metrics", self.export_csv),
            ("TXT summary", self.export_txt),
            ("Bitstream", self.export_bits),
        ]

        for index, (label, command) in enumerate(actions):
            self.main_button(box, label, command).grid(
                row=0,
                column=index,
                padx=10,
                pady=18,
                sticky="ew",
            )

        self.export_label = ctk.CTkLabel(
            frame,
            text="No export generated.",
            font=self.f,
            text_color=C["muted"],
        )
        self.export_label.grid(row=row + 1, column=0, padx=20, pady=18, sticky="w")

    # COMPARE / EXPORT
    def pick_compare(self, slot):
        path = filedialog.askopenfilename(
            title=f"Load file {slot}",
            filetypes=[
                ("Data files", "*.jsonl *.json *.txt *.csv *.bin *.raw *.dat *.log"),
                ("All files", "*.*"),
            ],
        )

        if not path:
            return

        values = load_file(path)

        if not values:
            messagebox.showerror(
                "No valid data",
                f"File {slot} does not contain valid values.",
            )
            return

        if slot == "A":
            self.compare_a = values
            self.compare_a_name = pathlib.Path(path).name
        else:
            self.compare_b = values
            self.compare_b_name = pathlib.Path(path).name

        self.show("Compare")

    def export_folder(self):
        folder = filedialog.askdirectory(title="Choose export folder")

        if not folder:
            return None

        return pathlib.Path(folder)

    def export_json(self):
        folder = self.export_folder()

        if not folder:
            return

        path = folder / "entro_report.json"

        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "source": self.source,
                    "results": self.results,
                },
                file,
                indent=2,
            )

        self.export_label.configure(text=f"Saved: {path}", text_color=C["accent"])

    def export_csv(self):
        folder = self.export_folder()

        if not folder:
            return

        path = folder / "entro_metrics.csv"

        with open(path, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["dataset", "metric", "value"])

            for name, result in self.results.items():
                for metric, value in result.items():
                    writer.writerow([name, metric, value])

        self.export_label.configure(text=f"Saved: {path}", text_color=C["accent"])

    def export_txt(self):
        folder = self.export_folder()

        if not folder:
            return

        path = folder / "entro_summary.txt"

        with open(path, "w", encoding="utf-8") as file:
            file.write("entro(py) analysis summary\n")
            file.write("=" * 50 + "\n\n")

            for name, result in self.results.items():
                file.write(f"{name.upper()}\n")
                file.write("-" * 50 + "\n")

                for metric, value in result.items():
                    file.write(f"{metric}: {value}\n")

                file.write("\n")

        self.export_label.configure(text=f"Saved: {path}", text_color=C["accent"])

    def export_bits(self):
        if not self.active_dataset:
            return

        folder = self.export_folder()

        if not folder:
            return

        path = folder / f"bits_{self.active_dataset}.txt"
        path.write_text(bitstream(self.data[self.active_dataset]), encoding="utf-8")

        self.export_label.configure(text=f"Saved: {path}", text_color=C["accent"])

    # PLOTTING
    def draw_plot(self):
        datasets = {
            self.active_dataset: self.data[self.active_dataset],
        }

        self.draw_into(
            self.plot_box,
            self.plot_kind.get(),
            datasets,
        )

    def draw_compare(self):
        for widget in self.compare_info.winfo_children():
            widget.destroy()

        if not self.compare_a or not self.compare_b:
            for widget in self.compare_box.winfo_children():
                widget.destroy()

            ctk.CTkLabel(
                self.compare_box,
                text="Load two files to compare them.",
                font=self.f,
                text_color=C["muted"],
            ).grid(row=0, column=0, padx=24, pady=24)

            return

        pairs = [
            (self.compare_a_name, self.compare_a),
            (self.compare_b_name, self.compare_b),
        ]

        for column, (name, data) in enumerate(pairs):
            metrics = analyze(data)

            cramers_value = metrics["Cramér's V"]

            ctk.CTkLabel(
                self.compare_info,
                text=(
                    f"{name}\n"
                    f"Samples: {metrics['Samples']:,}\n"
                    f"Entropy: {metrics['Shannon entropy']:.6f}\n"
                    f"Cramér's V: {cramers_value:.6f}"
                ),
                font=self.f_bold,
                text_color=C["text"],
                justify="left",
            ).grid(row=0, column=column, padx=18, pady=16, sticky="w")

        self.draw_into(
            self.compare_box,
            self.compare_kind.get(),
            {
                "A": self.compare_a,
                "B": self.compare_b,
            },
        )

    def draw_into(self, parent, kind, datasets):
        for widget in parent.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(10.8, 5.6), dpi=100, facecolor=C["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["card"])

        ax.tick_params(colors=C["muted"], labelsize=11)
        ax.xaxis.label.set_color(C["text"])
        ax.yaxis.label.set_color(C["text"])
        ax.title.set_color(C["text"])

        for spine in ax.spines.values():
            spine.set_color(C["line"])

        for label, values in datasets.items():
            if kind == "Distribution":
                x, y = distribution(values)
                ax.plot(x, y, linewidth=1.8, label=label)
                ax.set(xlabel="Value", ylabel="Count")

            elif kind == "Autocorrelation":
                x, y = autocorrelation(values)
                ax.plot(x, y, linewidth=1.8, label=label)
                ax.axhline(0, linewidth=1.0)
                ax.set(xlabel="Lag", ylabel="Correlation")

            elif kind == "FFT Spectrum":
                x, y = fft_spectrum(values)

                if len(x) > 1:
                    ax.plot(x[1:], y[1:], linewidth=1.1, label=label)

                ax.set(xlabel="Normalized frequency", ylabel="Magnitude")

            elif kind == "Entropy Over Time":
                x, y = entropy_over_time(values)
                ax.plot(x, y, linewidth=1.8, label=label)
                ax.axhline(8.0, linestyle="--", linewidth=1.2)
                ax.set(xlabel="Sample index", ylabel="Entropy")

            elif kind == "Raw Sequence":
                ax.plot(clean(values)[:1000], linewidth=1.0, label=label)
                ax.set(xlabel="Sample index", ylabel="Value", ylim=(-5, 260))

            elif kind == "Mutual Information":
                x, y = mutual_information_by_lag(values)
                ax.plot(x, y, linewidth=1.8, label=label)
                ax.set(xlabel="Lag", ylabel="Mutual information")

        ax.set_title(kind, fontsize=15, fontweight="bold")
        ax.grid(True, alpha=0.22)

        legend = ax.legend()

        if legend:
            legend.get_frame().set_facecolor(C["card2"])
            legend.get_frame().set_edgecolor(C["line"])

            for text in legend.get_texts():
                text.set_color(C["text"])

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()

        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, padx=14, pady=14, sticky="nsew")


if __name__ == "__main__":
    app = EntroApp()
    app.mainloop()

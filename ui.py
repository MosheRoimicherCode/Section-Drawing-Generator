from __future__ import annotations

import contextlib
import io
import threading
import traceback
from pathlib import Path
from tkinter import BooleanVar, Button, Entry, Label, StringVar, Text, Tk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from config import OUTPUT_DIR, POLES_FILE, SECTION_TEMPLATES, SURVEY_FILE, TEMPLATES_DIR
from generate_sections import generate_sections


def detect_template_mapping(templates_dir: Path) -> dict[str, str]:
    """Build section_type -> template filename mapping from template_TYPE.dxf files."""
    mapping: dict[str, str] = {}
    if not templates_dir.exists():
        return mapping

    for path in sorted(templates_dir.glob("template_*.dxf")):
        section_type = path.stem.removeprefix("template_").strip()
        if section_type:
            mapping[section_type] = path.name
    return mapping


def mapping_to_text(mapping: dict[str, str]) -> str:
    """Convert mapping dictionary into editable TYPE=filename.dxf lines."""
    return "\n".join(f"{section_type}={filename}" for section_type, filename in mapping.items())


def parse_mapping_text(text: str) -> dict[str, str]:
    """Read TYPE=filename.dxf lines from the UI text box."""
    mapping: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Template mapping line {line_number} must be SECTION_TYPE=template_file.dxf")
        section_type, filename = line.split("=", 1)
        section_type = section_type.strip()
        filename = filename.strip()
        if not section_type or not filename:
            raise ValueError(f"Template mapping line {line_number} has an empty section type or filename")
        mapping[section_type] = filename
    return mapping


class SectionGeneratorUi:
    """Small Tkinter desktop UI for selecting inputs and running the generator."""

    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Section Drawing Generator")
        self.root.geometry("900x700")

        self.survey_var = StringVar(value=str(SURVEY_FILE))
        self.poles_var = StringVar(value=str(POLES_FILE))
        self.templates_var = StringVar(value=str(TEMPLATES_DIR))
        self.output_var = StringVar(value=str(OUTPUT_DIR))
        self.limit_var = StringVar(value="")
        self.debug_var = BooleanVar(value=True)

        self.mapping_text: Text
        self.log_text: ScrolledText
        self.generate_button: Button

        self.build_layout()
        self.load_initial_template_mapping()

    def build_layout(self) -> None:
        """Create the visible UI controls."""
        self.root.columnconfigure(1, weight=1)
        row = 0

        row = self.add_path_row(row, "Survey DXF", self.survey_var, self.browse_survey)
        row = self.add_path_row(row, "Poles Excel", self.poles_var, self.browse_poles)
        row = self.add_path_row(row, "Templates Folder", self.templates_var, self.browse_templates)
        row = self.add_path_row(row, "Output Folder", self.output_var, self.browse_output)

        Label(self.root, text="Limit").grid(row=row, column=0, sticky="w", padx=8, pady=4)
        Entry(self.root, textvariable=self.limit_var).grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        Label(self.root, text="Optional: generate only first N poles").grid(row=row, column=2, sticky="w", padx=8, pady=4)
        row += 1

        Label(self.root, text="Template Mapping").grid(row=row, column=0, sticky="nw", padx=8, pady=4)
        self.mapping_text = Text(self.root, height=8)
        self.mapping_text.grid(row=row, column=1, columnspan=2, sticky="nsew", padx=8, pady=4)
        self.root.rowconfigure(row, weight=1)
        row += 1

        Button(self.root, text="Detect Templates", command=self.refresh_template_mapping).grid(
            row=row, column=1, sticky="w", padx=8, pady=4
        )
        self.generate_button = Button(self.root, text="Generate", command=self.start_generate)
        self.generate_button.grid(row=row, column=2, sticky="e", padx=8, pady=4)
        row += 1

        Label(self.root, text="Run Log").grid(row=row, column=0, sticky="nw", padx=8, pady=4)
        self.log_text = ScrolledText(self.root, height=16)
        self.log_text.grid(row=row, column=1, columnspan=2, sticky="nsew", padx=8, pady=4)
        self.root.rowconfigure(row, weight=2)

    def add_path_row(self, row: int, label: str, variable: StringVar, command) -> int:
        """Add one file/folder chooser row."""
        Label(self.root, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        Entry(self.root, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        Button(self.root, text="Browse", command=command).grid(row=row, column=2, sticky="ew", padx=8, pady=4)
        return row + 1

    def browse_survey(self) -> None:
        """Select the survey DXF file."""
        path = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")])
        if path:
            self.survey_var.set(path)

    def browse_poles(self) -> None:
        """Select the poles Excel file."""
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if path:
            self.poles_var.set(path)

    def browse_templates(self) -> None:
        """Select the folder containing template DXF files."""
        path = filedialog.askdirectory()
        if path:
            self.templates_var.set(path)
            self.refresh_template_mapping()

    def browse_output(self) -> None:
        """Select the folder where generated DXFs and run reports will be saved."""
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)

    def load_initial_template_mapping(self) -> None:
        """Load config mapping first, then replace it with detected templates if any exist."""
        detected = detect_template_mapping(Path(self.templates_var.get()))
        mapping = detected or SECTION_TEMPLATES
        self.mapping_text.delete("1.0", "end")
        self.mapping_text.insert("1.0", mapping_to_text(mapping))

    def refresh_template_mapping(self) -> None:
        """Scan selected templates folder for template_TYPE.dxf files."""
        mapping = detect_template_mapping(Path(self.templates_var.get()))
        self.mapping_text.delete("1.0", "end")
        self.mapping_text.insert("1.0", mapping_to_text(mapping))
        self.append_log(f"Detected {len(mapping)} template mapping(s).\n")

    def append_log(self, message: str) -> None:
        """Append text to the run log box."""
        self.log_text.insert("end", message)
        self.log_text.see("end")

    def read_limit(self) -> int | None:
        """Parse the optional limit field."""
        value = self.limit_var.get().strip()
        if not value:
            return None
        return int(value)

    def start_generate(self) -> None:
        """Validate UI input and run generation on a background thread."""
        try:
            section_templates = parse_mapping_text(self.mapping_text.get("1.0", "end"))
            limit = self.read_limit()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.generate_button.config(state="disabled")
        self.log_text.delete("1.0", "end")
        self.append_log("Starting generation...\n")

        thread = threading.Thread(
            target=self.run_generate,
            kwargs={
                "survey_file": self.survey_var.get(),
                "poles_file": self.poles_var.get(),
                "templates_dir": self.templates_var.get(),
                "output_dir": self.output_var.get(),
                "section_templates": section_templates,
                "limit": limit,
            },
            daemon=True,
        )
        thread.start()

    def run_generate(self, **kwargs) -> None:
        """Run generator and send stdout or errors back to the UI thread."""
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                generate_sections(debug=True, **kwargs)
            output = buffer.getvalue()
            self.root.after(0, self.finish_generate, output, None)
        except Exception:
            output = buffer.getvalue() + "\n" + traceback.format_exc()
            self.root.after(0, self.finish_generate, output, "Generation failed")

    def finish_generate(self, output: str, error_title: str | None) -> None:
        """Re-enable the button and show the final result."""
        self.append_log(output)
        self.generate_button.config(state="normal")
        if error_title:
            messagebox.showerror(error_title, "Check the run log for details.")
        else:
            messagebox.showinfo("Done", "Generation finished. Check the output folder.")

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()


if __name__ == "__main__":
    SectionGeneratorUi().run()

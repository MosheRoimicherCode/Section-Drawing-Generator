# Automated Railway Pole Section Drawing Generator

Generates CAD cross-section DXF drawings for railway overhead line pole sections from:

- `survey.dxf`: 3D survey DXF containing arm polylines by layer.
- `poles.xlsx`: pole list with `pole_number`, `X`, `Y`, and `section_type` columns.
- `templates/template_TYPE*.dxf`: section templates containing DIMENSION text override placeholders.

The generator measures each 3D arm polyline, assigns it to the nearest pole, classifies it as left or right by X position, copies the matching section template, and replaces DIMENSION text override placeholders with measured values.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Expected Structure

```text
Section Drawing Generator/
  survey.dxf
  poles.xlsx
  templates/
    template_TYPE1.dxf
    template_TYPE2.dxf
  output/
  config.py
  generate_sections.py
  requirements.txt
```

## Run

```powershell
python generate_sections.py --debug
```

Use `--limit 1` for a first template replacement test on one pole pair.

```powershell
python generate_sections.py --debug --limit 1
```

## Template Placeholders

Template DXF DIMENSION entities should use text overrides such as `CANTI_L`, `CANTI_R`, `CW_L`, `CW_R`, `RW_L`, `RW_R`, and `POLE_NUM`. The script only changes `dim.dxf.text`; it does not re-render dimensions.

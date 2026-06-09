from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SURVEY_FILE = "C:/Users/user/Downloads/Drawing2.dxf"
POLES_FILE = BASE_DIR / "POLES.xlsx"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"

# Map: layer name in survey DXF -> placeholder IDs (left, right)
ARM_LAYERS = {
    "canti_7_1": ("canti_7_1"),
    "canti_7_2": ("canti_7_2"),
    "canti_7_3": ("canti_7_3"),
    "canti_7_4": ("canti_7_4"),
    "canti_7_5": ("canti_7_5"),
    "canti_7_6": ("canti_7_6"), 
    "canti_H": ("canti_H"),
    "cw_hight": ("cw_hight"),
    "pole_rail": ("pole_rail"),
    "PRM": ("PRM"),
    "sys_H": ("sys_H"),
    "cw_stagger": ("cw_stagger"),
    "Soil_l": ("Soil_l"),
    "Mes_p": ("Mes_p"),

}

# Map: section_type value in Excel -> template filename
SECTION_TEMPLATES = {
    "TYPE1": "template_TYPE1.dxf",
    "TYPE2": "template_TYPE2.dxf",
}

# DXF survey units are meters. Measured output text is formatted in meters.
SURVEY_TO_OUTPUT_UNITS = 1000

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SURVEY_FILE = "C:/Users/user/Downloads/Drawing2.dxf"
POLES_FILE = BASE_DIR / "POLES.xlsx"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"

# Map: layer name in survey DXF -> placeholder IDs (left, right)
ARM_LAYERS = {
    "CANTI_L": ("CANTI_L"),
    "CANTI_R": ("CANTI_R"),
    
    "CANTI_L_2": ("CANTI_L_2"),
    "CANTI_R_2": ("CANTI_R_2"),

    "CW_L": ("CW_L"),
    "CW_R": ("CW_R"),

    "RW_L": ("RW_L"),
    "RW_R": ("RW_R"),

    "MW_L": ("MW_L"),
    "MW_R": ("MW_R"),
}

# Map: section_type value in Excel -> template filename
SECTION_TEMPLATES = {
    "TYPE1": "template_TYPE1.dxf",
    "TYPE2": "template_TYPE2.dxf",
}

# DXF survey units are meters; output dimension text is millimeters.
SURVEY_TO_OUTPUT_UNITS = 1000

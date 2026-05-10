"""Add glossary_entries table with seed data

Revision ID: 003
Revises: 002
Create Date: 2026-05-09
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

# Seed data embedded in migration for repeatability
SEED_DATA = [
    {"abbreviation": "FRL", "expansion": "Freightliner", "category": "make", "source": "seed"},
    {"abbreviation": "PB", "expansion": "Peterbilt", "category": "make", "source": "seed"},
    {"abbreviation": "Pete", "expansion": "Peterbilt", "category": "make", "source": "seed"},
    {"abbreviation": "KW", "expansion": "Kenworth", "category": "make", "source": "seed"},
    {"abbreviation": "INT", "expansion": "International", "category": "make", "source": "seed"},
    {"abbreviation": "Navistar", "expansion": "International", "category": "make", "source": "seed"},
    {"abbreviation": "MACK", "expansion": "Mack Trucks", "category": "make", "source": "seed"},
    {"abbreviation": "WS", "expansion": "Western Star", "category": "make", "source": "seed"},
    {"abbreviation": "HYND", "expansion": "Hyundai Translead", "category": "make", "source": "seed"},
    {"abbreviation": "UTIL", "expansion": "Utility Trailer", "category": "make", "source": "seed"},
    {"abbreviation": "GDN", "expansion": "Great Dane", "category": "make", "source": "seed"},
    {"abbreviation": "WBSH", "expansion": "Wabash", "category": "make", "source": "seed"},
    {"abbreviation": "STGH", "expansion": "Stoughton", "category": "make", "source": "seed"},
    {"abbreviation": "VANG", "expansion": "Vanguard", "category": "make", "source": "seed"},
    {"abbreviation": "HINO", "expansion": "Hino", "category": "make", "source": "seed"},
    {"abbreviation": "Casc", "expansion": "Cascadia", "category": "model", "source": "seed"},
    {"abbreviation": "T680", "expansion": "Kenworth T680", "category": "model", "source": "seed"},
    {"abbreviation": "T880", "expansion": "Kenworth T880", "category": "model", "source": "seed"},
    {"abbreviation": "W900", "expansion": "Kenworth W900", "category": "model", "source": "seed"},
    {"abbreviation": "579", "expansion": "Peterbilt 579", "category": "model", "source": "seed"},
    {"abbreviation": "389", "expansion": "Peterbilt 389", "category": "model", "source": "seed"},
    {"abbreviation": "VNL", "expansion": "Volvo VNL", "category": "model", "source": "seed"},
    {"abbreviation": "VNR", "expansion": "Volvo VNR", "category": "model", "source": "seed"},
    {"abbreviation": "LT", "expansion": "International LT", "category": "model", "source": "seed"},
    {"abbreviation": "Prostar", "expansion": "International ProStar", "category": "model", "source": "seed"},
    {"abbreviation": "Anthem", "expansion": "Mack Anthem", "category": "model", "source": "seed"},
    {"abbreviation": "Pinnacle", "expansion": "Mack Pinnacle", "category": "model", "source": "seed"},
    {"abbreviation": "DD13", "expansion": "Detroit Diesel DD13", "category": "engine", "source": "seed"},
    {"abbreviation": "DD15", "expansion": "Detroit Diesel DD15", "category": "engine", "source": "seed"},
    {"abbreviation": "DD16", "expansion": "Detroit Diesel DD16", "category": "engine", "source": "seed"},
    {"abbreviation": "X15", "expansion": "Cummins X15", "category": "engine", "source": "seed"},
    {"abbreviation": "X12", "expansion": "Cummins X12", "category": "engine", "source": "seed"},
    {"abbreviation": "ISX", "expansion": "Cummins ISX", "category": "engine", "source": "seed"},
    {"abbreviation": "ISX15", "expansion": "Cummins ISX15", "category": "engine", "source": "seed"},
    {"abbreviation": "MX-13", "expansion": "Paccar MX-13", "category": "engine", "source": "seed"},
    {"abbreviation": "MX13", "expansion": "Paccar MX-13", "category": "engine", "source": "seed"},
    {"abbreviation": "D13", "expansion": "Volvo D13", "category": "engine", "source": "seed"},
    {"abbreviation": "MP8", "expansion": "Mack MP8", "category": "engine", "source": "seed"},
    {"abbreviation": "N13", "expansion": "Navistar N13", "category": "engine", "source": "seed"},
    {"abbreviation": "reefer", "expansion": "refrigerated trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "flatbed", "expansion": "flatbed trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "stepdeck", "expansion": "step deck trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "dry van", "expansion": "dry van trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "tanker", "expansion": "tanker trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "lowboy", "expansion": "lowboy trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "hotshot", "expansion": "hotshot trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "conestoga", "expansion": "conestoga trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "daycab", "expansion": "day cab tractor", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "sleeper", "expansion": "sleeper cab tractor", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "bobtail", "expansion": "truck without trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "B-train", "expansion": "B-train double trailer", "category": "vehicle_type", "source": "seed"},
    {"abbreviation": "DOT", "expansion": "Department of Transportation", "category": "general", "source": "seed"},
    {"abbreviation": "APU", "expansion": "auxiliary power unit", "category": "general", "source": "seed"},
    {"abbreviation": "DPF", "expansion": "diesel particulate filter", "category": "general", "source": "seed"},
    {"abbreviation": "DEF", "expansion": "diesel exhaust fluid", "category": "general", "source": "seed"},
    {"abbreviation": "EGR", "expansion": "exhaust gas recirculation", "category": "general", "source": "seed"},
    {"abbreviation": "SCR", "expansion": "selective catalytic reduction", "category": "general", "source": "seed"},
    {"abbreviation": "OTR", "expansion": "over the road", "category": "general", "source": "seed"},
    {"abbreviation": "CDL", "expansion": "commercial driver's license", "category": "general", "source": "seed"},
    {"abbreviation": "GVWR", "expansion": "gross vehicle weight rating", "category": "general", "source": "seed"},
    {"abbreviation": "GCW", "expansion": "gross combination weight", "category": "general", "source": "seed"},
    {"abbreviation": "WB", "expansion": "wheelbase", "category": "general", "source": "seed"},
    {"abbreviation": "TA", "expansion": "tandem axle", "category": "general", "source": "seed"},
    {"abbreviation": "SA", "expansion": "single axle", "category": "general", "source": "seed"},
    {"abbreviation": "ELD", "expansion": "electronic logging device", "category": "general", "source": "seed"},
    {"abbreviation": "PM", "expansion": "preventive maintenance", "category": "general", "source": "seed"},
    {"abbreviation": "DOC", "expansion": "diesel oxidation catalyst", "category": "general", "source": "seed"},
    {"abbreviation": "VIN", "expansion": "vehicle identification number", "category": "general", "source": "seed"},
    {"abbreviation": "ECM", "expansion": "engine control module", "category": "general", "source": "seed"},
    {"abbreviation": "CARB", "expansion": "California Air Resources Board", "category": "general", "source": "seed"},
    {"abbreviation": "EPA", "expansion": "Environmental Protection Agency", "category": "general", "source": "seed"},
    {"abbreviation": "OBO", "expansion": "or best offer", "category": "general", "source": "seed"},
    {"abbreviation": "K", "expansion": "thousand (miles or dollars)", "category": "unit", "source": "seed"},
    {"abbreviation": "mi", "expansion": "miles", "category": "unit", "source": "seed"},
]


def upgrade():
    glossary_table = op.create_table(
        "glossary_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("abbreviation", sa.String(collation="NOCASE"), nullable=False),
        sa.Column("expansion", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="seed"),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("usage_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_glossary_entries_abbreviation", "glossary_entries", ["abbreviation"], unique=True)

    op.bulk_insert(glossary_table, SEED_DATA)


def downgrade():
    op.drop_table("glossary_entries")

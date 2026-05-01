import io
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def build_xlsx(app_name, profils, droits, valeurs_cache, hab_cache):
    wb = Workbook()
    ws = wb.active
    ws.title = "Matrice"

    fill_header = PatternFill("solid", fgColor="37306E")
    fill_profil = PatternFill("solid", fgColor="042638")
    fill_oui    = PatternFill("solid", fgColor="4CBFDC")
    fill_non    = PatternFill("solid", fgColor="FFF5E9")
    fill_titre  = PatternFill("solid", fgColor="EA4D49")

    font_white_bold = Font(name="Arial", bold=True, color="FFFFFF")
    font_dark       = Font(name="Arial", color="042638")
    font_titre      = Font(name="Arial", bold=True, color="FFFFFF", size=14)

    thin   = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Titre
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(droits) + 1)
    tc = ws.cell(row=1, column=1, value=f"Matrice des habilitations — {app_name}")
    tc.fill, tc.font, tc.alignment = fill_titre, font_titre, center
    ws.row_dimensions[1].height = 30

    # En-têtes droits
    h = ws.cell(row=2, column=1, value="Profil \\ Droit")
    h.fill, h.font, h.alignment, h.border = fill_header, font_white_bold, center, border
    for j, d in enumerate(droits):
        c = ws.cell(row=2, column=j + 2, value=d["nom"])
        c.fill, c.font, c.alignment, c.border = fill_header, font_white_bold, center, border
    ws.row_dimensions[2].height = 40

    # Lignes profils
    for i, p in enumerate(profils):
        row = i + 3
        pc = ws.cell(row=row, column=1, value=p["nom"])
        pc.fill, pc.font, pc.alignment, pc.border = fill_profil, font_white_bold, center, border
        ws.row_dimensions[row].height = 22

        for j, d in enumerate(droits):
            val  = hab_cache.get((p["id"], d["id"]))
            col  = j + 2
            if d["type_valeur"] == "booleen":
                display = "Oui" if str(val) == "1" else "Non"
                fill    = fill_oui if str(val) == "1" else fill_non
            else:
                display = val if val else "—"
                fill    = fill_oui if val else fill_non
            cell = ws.cell(row=row, column=col, value=display)
            cell.fill, cell.font, cell.alignment, cell.border = fill, font_dark, center, border

    ws.column_dimensions[get_column_letter(1)].width = 22
    for j in range(len(droits)):
        ws.column_dimensions[get_column_letter(j + 2)].width = 16

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()

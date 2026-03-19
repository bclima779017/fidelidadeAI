import os
from datetime import datetime
import pandas as pd
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def generate_report(results: list[dict]) -> str:
    """Gera o relatório .xlsx com formatação condicional e retorna o caminho do arquivo."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filepath = os.path.join(OUTPUT_DIR, f"auditoria_{timestamp}.xlsx")

    df = pd.DataFrame(results, columns=[
        "Pergunta",
        "Resposta Oficial",
        "Resposta IA",
        "Score",
        "Justificativa",
    ])

    avg_score = df["Score"].mean()
    min_score = df["Score"].min()
    max_score = df["Score"].max()
    min_idx = df["Score"].idxmin() + 1
    max_idx = df["Score"].idxmax() + 1

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Resultados", index=False, startrow=1)
        ws = writer.sheets["Resultados"]

        # Título
        ws.merge_cells("A1:E1")
        title_cell = ws["A1"]
        title_cell.value = f"Auditoria GEO — Kípiai — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        title_cell.font = Font(bold=True, size=14, color="1F4E79")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        # Estilo do header
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        for col in range(1, 6):
            cell = ws.cell(row=2, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", wrap_text=True)

        # Formatação condicional por score
        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        green_font = Font(color="006100", bold=True)
        yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        yellow_font = Font(color="9C6500", bold=True)
        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        red_font = Font(color="9C0006", bold=True)

        for row in range(3, 3 + len(df)):
            score_cell = ws.cell(row=row, column=4)
            score_val = score_cell.value
            if score_val is not None and score_val != "":
                try:
                    score_num = int(score_val)
                except (ValueError, TypeError):
                    continue
                if score_num >= 70:
                    score_cell.fill = green_fill
                    score_cell.font = green_font
                elif score_num >= 50:
                    score_cell.fill = yellow_fill
                    score_cell.font = yellow_font
                else:
                    score_cell.fill = red_fill
                    score_cell.font = red_font
                score_cell.alignment = Alignment(horizontal="center")

        # Larguras de coluna
        col_widths = {"A": 40, "B": 45, "C": 45, "D": 10, "E": 50}
        for col_letter, width in col_widths.items():
            ws.column_dimensions[col_letter].width = width

        # Bordas finas
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        for row in ws.iter_rows(min_row=2, max_row=2 + len(df), min_col=1, max_col=5):
            for cell in row:
                cell.border = thin_border
                if cell.column != 4:
                    cell.alignment = Alignment(wrap_text=True, vertical="top")

        # Linha de resumo
        summary_row = 3 + len(df) + 1
        ws.merge_cells(f"A{summary_row}:C{summary_row}")
        ws.cell(row=summary_row, column=1).value = "RESUMO DA AUDITORIA"
        ws.cell(row=summary_row, column=1).font = Font(bold=True, size=12, color="1F4E79")

        metrics = [
            (summary_row + 1, "Score Médio", f"{avg_score:.1f}"),
            (summary_row + 2, "Score Mínimo", f"{min_score} (Pergunta {min_idx})"),
            (summary_row + 3, "Score Máximo", f"{max_score} (Pergunta {max_idx})"),
            (summary_row + 4, "Total de Perguntas", str(len(df))),
            (summary_row + 5, "Erros (score = -1)", str(len(df[df["Score"] == -1]))),
        ]
        for row_num, label, value in metrics:
            ws.cell(row=row_num, column=1).value = label
            ws.cell(row=row_num, column=1).font = Font(bold=True)
            ws.cell(row=row_num, column=2).value = value

    return filepath

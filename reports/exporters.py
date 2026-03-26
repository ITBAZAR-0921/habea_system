from __future__ import annotations

from io import BytesIO

from django.http import HttpResponse


def _tab_config(tab: str):
    if tab == 'notices':
        return {
            'title': 'Мэдэгдлийн тайлан',
            'headers': ['Мэдэгдлийн нэр', 'Нийт ажилтан', 'Танилцсан', 'Танилцаагүй'],
            'row_builder': lambda row: [row['title'], row['total_employees'], row['read_count'], row['unread_count']],
        }
    if tab == 'instructions':
        return {
            'title': 'Зааварчилгааны тайлан',
            'headers': ['Зааварчилгааны нэр', 'Нийт ажилтан', 'Танилцсан', 'Хугацаа дууссан', '30 хоногт дуусах'],
            'row_builder': lambda row: [
                row['title'],
                row['total_employees'],
                row['acknowledged'],
                row['overdue'],
                row['due_soon'],
            ],
        }
    if tab == 'trainings':
        return {
            'title': 'Сургалтын тайлан',
            'headers': ['Сургалтын нэр', 'Нийт хамрагдах', 'Дууссан %', 'Дуусаагүй %'],
            'row_builder': lambda row: [
                row['title'],
                row['total_target'],
                row['completed_percent'],
                row['incomplete_percent'],
            ],
        }
    return {
        'title': 'Шалгалтын тайлан',
        'headers': ['Шалгалтын нэр', 'Хамрагдсан', 'Дундаж оноо', 'Тэнцсэн %', 'Унасан %'],
        'row_builder': lambda row: [
            row['title'],
            row['participated'],
            row['avg_score'],
            row['passed_percent'],
            row['failed_percent'],
        ],
    }


def export_tab_to_excel(tab: str, tab_data: dict):
    from openpyxl import Workbook

    config = _tab_config(tab)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Report'

    sheet.append([config['title']])
    sheet.append([])
    sheet.append(config['headers'])

    for row in tab_data['rows']:
        sheet.append(config['row_builder'](row))

    for col in sheet.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            value = '' if cell.value is None else str(cell.value)
            max_length = max(max_length, len(value))
        sheet.column_dimensions[col_letter].width = min(max_length + 2, 60)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    filename = f'{tab}_report.xlsx'
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_tab_to_pdf(tab: str, tab_data: dict):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    config = _tab_config(tab)

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    try:
        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        base_font = 'DejaVuSans'
    except Exception:
        base_font = 'Helvetica'

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontName = base_font

    table_data = [config['headers']]
    for row in tab_data['rows']:
        table_data.append([str(item) for item in config['row_builder'](row)])

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ('FONTNAME', (0, 0), (-1, -1), base_font),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    story = [Paragraph(config['title'], title_style), Spacer(1, 8), table]
    document.build(story)

    filename = f'{tab}_report.pdf'
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

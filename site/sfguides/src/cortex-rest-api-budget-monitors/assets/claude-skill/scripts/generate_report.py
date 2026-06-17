import argparse
import json
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def make_daily_chart(daily_data):
    fig, ax = plt.subplots(figsize=(7, 3))
    dates = [d['usage_date'] for d in daily_data]
    tokens = [d['total_tokens'] for d in daily_data]
    ax.bar(range(len(dates)), tokens, color='#29B5E8')
    ax.set_xticks(range(0, len(dates), max(1, len(dates) // 6)))
    ax.set_xticklabels([dates[i] for i in range(0, len(dates), max(1, len(dates) // 6))], rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('Tokens')
    ax.set_title('Daily Token Usage')
    ax.ticklabel_format(style='plain', axis='y')
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def make_model_chart(model_data):
    fig, ax = plt.subplots(figsize=(7, 3))
    models = [d['model_name'] for d in model_data]
    tokens = [d['total_tokens'] for d in model_data]
    ax.barh(models, tokens, color='#FF6F61')
    ax.set_xlabel('Tokens')
    ax.set_title('Tokens by Model')
    ax.ticklabel_format(style='plain', axis='x')
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_pdf(totals, daily, by_model, daily_by_model, start_date, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('ReportTitle', parent=styles['Title'], fontSize=20, spaceAfter=12)
    heading_style = ParagraphStyle('ReportHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=8, spaceBefore=16)

    elements = []

    elements.append(Paragraph('Cortex REST API Usage Report', title_style))
    elements.append(Paragraph(f'Period: {start_date} to {datetime.now().strftime("%Y-%m-%d")}', styles['Normal']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph('KPI Summary', heading_style))
    total_tokens = totals.get('total_tokens', 0) or 0
    total_requests = totals.get('total_requests', 0) or 0
    unique_models = totals.get('unique_models', 0) or 0
    kpi_data = [
        ['Total Tokens', 'Total Requests', 'Unique Models'],
        [f'{int(total_tokens):,}', f'{int(total_requests):,}', str(int(unique_models))],
    ]
    kpi_table = Table(kpi_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#29B5E8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 16))

    if daily:
        elements.append(Paragraph('Daily Token Usage', heading_style))
        chart_buf = make_daily_chart(daily)
        elements.append(Image(chart_buf, width=6.5*inch, height=2.8*inch))
        elements.append(Spacer(1, 12))

    if by_model:
        elements.append(Paragraph('Tokens by Model', heading_style))
        chart_buf = make_model_chart(by_model)
        elements.append(Image(chart_buf, width=6.5*inch, height=2.8*inch))
        elements.append(Spacer(1, 12))

    if daily_by_model:
        elements.append(Paragraph('Daily Usage by Model', heading_style))
        header = ['Date', 'Model', 'Tokens', 'Requests']
        rows = [header]
        for d in daily_by_model[:50]:
            rows.append([
                str(d.get('usage_date', '')),
                str(d.get('model_name', '')),
                f'{int(d.get("total_tokens", 0)):,}',
                str(d.get('request_count', '')),
            ])
        t = Table(rows, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#29B5E8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F8FF')]),
        ]))
        elements.append(t)

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Italic']))

    doc.build(elements)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Generate Cortex REST API usage PDF report')
    parser.add_argument('--totals', required=True, help='JSON string with total_tokens, total_requests, unique_models')
    parser.add_argument('--daily', required=True, help='JSON array of {usage_date, total_tokens, request_count}')
    parser.add_argument('--by-model', required=True, help='JSON array of {model_name, total_tokens, request_count}')
    parser.add_argument('--daily-by-model', required=True, help='JSON array of {usage_date, model_name, total_tokens}')
    parser.add_argument('--start-date', required=True, help='Report start date (e.g., 2025-02-13)')
    parser.add_argument('--output', required=True, help='Output PDF file path')
    args = parser.parse_args()

    totals = json.loads(args.totals)
    daily = json.loads(args.daily)
    by_model = json.loads(args.by_model)
    daily_by_model = json.loads(args.daily_by_model)

    output = generate_pdf(totals, daily, by_model, daily_by_model, args.start_date, args.output)
    print(f'Report generated: {output}')


if __name__ == '__main__':
    main()

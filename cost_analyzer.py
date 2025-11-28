from flask import Flask, render_template_string, request, send_file
import boto3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64
import json
import pandas as pd
from fpdf import FPDF
import os

app = Flask(__name__)

# --- CONFIGURATION CONSTANTS ---
RUPEE_RATE = 83.00 
ALERT_THRESHOLD_INR = 500.00

# 🛑 IMPORTANT: Inga unga SNS Topic ARN-a kandippa podunga!
SNS_TOPIC_ARN = "YOUR_SNS_TOPIC_ARN_HERE" 

# Default Dates
TODAY = datetime.today().strftime('%Y-%m-%d')
FIRST_DAY_OF_MONTH = datetime.today().replace(day=1).strftime('%Y-%m-%d')

# --- SNS ALERT FUNCTION (Modified to send mail always) ---
def send_sns_alert(aws_access_key_id, aws_secret_access_key, region_name, total_in_rupees, start_date, end_date):
    # Check if ARN is updated
    if "YOUR_SNS_TOPIC_ARN_HERE" in SNS_TOPIC_ARN:
        print("❌ Error: SNS Topic ARN update pannunga code-la!")
        return False

    try:
        sns_client = boto3.client(
            'sns',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # Subject line varies based on cost
        if total_in_rupees > ALERT_THRESHOLD_INR:
            subject = f"🚨 HIGH COST ALERT: ₹{total_in_rupees:,.2f}"
            status = "WARNING: Usage is high."
        else:
            subject = f"✅ AWS Cost Update: ₹{total_in_rupees:,.2f}"
            status = "Good Job! Usage is under control."

        message = (
            f"AWS Cost Analyzer Report\n"
            f"------------------------\n"
            f"Date Range: {start_date} to {end_date}\n"
            f"Total Cost: ₹{total_in_rupees:,.2f}\n\n"
            f"Status: {status}\n"
        )
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject
        )
        return True
    except Exception as e:
        print(f"Error sending SNS alert: {e}")
        return False


# --- CHART GENERATION ---
def generate_cost_chart(report_data):
    if not report_data: return None
    services = [item['Service'] for item in report_data]
    costs = [float(item['Cost (INR)'].replace('₹', '').replace(',', '')) for item in report_data]

    plt.figure(figsize=(10, 6), facecolor='none') 
    ax = plt.axes()
    ax.set_facecolor('none')
    
    bar_colors = ['#065f46', '#34d399', '#10b981', '#059669', '#6ee7b7']
    bars = plt.bar(services, costs, color=bar_colors[:len(services)])
    
    text_color = '#1f2937' 
    plt.ylabel('Cost (INR)', fontsize=12, color=text_color)
    plt.title('Cost Breakdown', fontsize=14, color=text_color)
    ax.tick_params(colors=text_color)
    for spine in ax.spines.values(): spine.set_color(text_color)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'Rs.{yval:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color=text_color)
    
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', transparent=True)
    plt.close()
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# --- PDF GENERATION ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'AWS Cost Report', 0, 1, 'C'); self.ln(10)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(data, start_date, end_date, total_in_rupees):
    pdf = PDFReport(); pdf.add_page(); pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Date: {start_date} to {end_date}', 0, 1)
    pdf.set_font('Arial', 'B', 14); pdf.set_text_color(16, 185, 129)
    pdf.cell(0, 10, f'Total: {total_in_rupees.replace("₹", "Rs. ")}', 0, 1)
    pdf.set_text_color(0); pdf.ln(5)
    pdf.set_fill_color(16, 185, 129); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 10)
    pdf.cell(80, 10, 'Service', 1, 0, 'C', 1); pdf.cell(50, 10, 'INR', 1, 0, 'C', 1); pdf.cell(50, 10, 'USD', 1, 1, 'C', 1)
    pdf.set_text_color(0); pdf.set_font('Arial', '', 10)
    for row in data:
        pdf.cell(80, 10, row['Service'], 1, 0, 'L'); pdf.cell(50, 10, row['Cost (INR)'].replace("₹", "Rs. "), 1, 0, 'R'); pdf.cell(50, 10, row['Cost (USD)'], 1, 1, 'R')
    
    buf = io.BytesIO(); buf.write(pdf.output(dest='S').encode('latin-1')); buf.seek(0); return buf

# --- CORE LOGIC ---
def fetch_cost_data(key, secret, region, start, end):
    if not start or not end: return {'error': "Dates required"}
    try: exc_end = (datetime.strptime(end, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    except: return {'error': "Invalid Date"}

    try:
        client = boto3.client('ce', aws_access_key_id=key, aws_secret_access_key=secret, region_name=region)
        resp = client.get_cost_and_usage(TimePeriod={'Start': start, 'End': exc_end}, Granularity='MONTHLY', Metrics=['UnblendedCost'], GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}])
        total, r_data = 0.0, []
        for res in resp['ResultsByTime']:
            for grp in res['Groups']:
                cost = float(grp['Metrics']['UnblendedCost']['Amount'])
                if cost > 0.00:
                    r_data.append({'Service': grp['Keys'][0].strip(), 'Cost (INR)': f"₹{cost*RUPEE_RATE:,.2f}", 'Cost (USD)': f"${cost:.2f}"})
                    total += cost
        
        tot_inr = total * RUPEE_RATE
        alert = tot_inr > ALERT_THRESHOLD_INR
        msg = f"⚠️ ALERT: ₹{tot_inr:,.2f}" if alert else f"✅ Good Job! Total: ₹{tot_inr:,.2f}"
        
        # ✅ CHANGE: Always send email, regardless of cost amount
        sent = send_sns_alert(key, secret, region, tot_inr, start, end)
        
        return {'start_date': start, 'end_date': end, 'report_data': r_data, 'total_in_rupees': f"₹{tot_inr:,.2f}", 'chart_base64': generate_cost_chart(r_data), 'is_alert': alert, 'status_message': msg, 'email_alert_sent': sent}
    except Exception as e: return {'error': str(e)}

# --- HTML TEMPLATE (MINT GREEN) ---
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Cost Analyzer</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg-start: #84fab0; --bg-end: #8fd3f4; --glass-bg: rgba(255,255,255,0.7); --text: #064e3b; --btn: #10b981; }
        body { font-family: 'Poppins', sans-serif; background: linear-gradient(120deg, var(--bg-start), var(--bg-end)); min-height: 100vh; margin: 0; padding: 20px; color: var(--text); display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 1100px; margin: 20px auto; }
        h1 { font-size: 2.8rem; color: #1f2937; text-align: center; } h1 span { color: #059669; }
        .card { background: var(--glass-bg); backdrop-filter: blur(12px); border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); padding: 30px; margin-bottom: 30px; }
        input, select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #a7f3d0; margin-bottom: 20px; box-sizing: border-box; }
        .btn { width: 100%; padding: 14px; background: var(--btn); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 1rem; }
        .btn:hover { background: #059669; }
        .total-display { font-size: 3rem; font-weight: 800; color: #059669; margin: 10px 0; text-align: center; }
        .status-bar { padding: 15px; border-radius: 8px; margin-top: 10px; font-weight: 600; text-align: center; background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
        .chart-container { text-align: center; margin: 30px 0; background: rgba(255,255,255,0.4); border-radius: 10px; padding: 20px; }
        .chart-container img { max-width: 100%; height: auto; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
        th { background: #ecfdf5; color: #064e3b; padding: 15px; text-align: left; }
        td { padding: 15px; border-bottom: 1px solid #f0fdf4; }
        .flex-row { display: flex; gap: 20px; } .flex-col { flex: 1; }
        .download-section { text-align: center; margin-top: 20px; }
        .download-controls { display: flex; gap: 15px; justify-content: center; margin-top: 15px; }
        .btn-download { background: transparent; color: #064e3b; border: 2px solid #064e3b; width: auto; padding: 10px 25px; }
        .btn-download:hover { background: #064e3b; color: white; }
        @media (max-width: 768px) { .flex-row { flex-direction: column; gap: 0; } }
    </style>
</head>
<body>
<div class="container">
    <header><h1>AWS Cloud <span>Cost Analyzer</span></h1></header>
    <div class="card">
        <form method="POST">
            <label>Access Key ID</label><input type="text" name="key_id" required>
            <label>Secret Key</label><input type="password" name="secret_key" required>
            <label>Region</label><input type="text" name="region" value="us-east-1" required>
            <div class="flex-row">
                <div class="flex-col"><label>Start Date</label><input type="date" name="start_date" value="{{ FIRST_DAY_OF_MONTH }}" required></div>
                <div class="flex-col"><label>End Date</label><input type="date" name="end_date" value="{{ TODAY }}" required></div>
            </div>
            <input type="submit" value="🚀 Analyze Costs" class="btn">
        </form>
    </div>
    {% if results.error %}<div class="card" style="color: red;">⚠️ {{ results.error }}</div>{% endif %}
    {% if results.report_data %}
    <div class="card">
        <div style="text-align: center;">{{ results.start_date }} — {{ results.end_date }}</div>
        <div class="total-display">{{ results.total_in_rupees }}</div>
        <div style="text-align: center; font-weight: bold; color: {{ 'red' if results.is_alert else 'green' }};">{{ results.status_message }}</div>
        
        {% if results.email_alert_sent %}
            <div style="text-align: center; color: green; margin-top: 5px;">📧 Email Report Sent Successfully!</div>
        {% else %}
            <div style="text-align: center; color: red; margin-top: 5px;">❌ Email Not Sent (Check SNS ARN)</div>
        {% endif %}

        {% if results.chart_base64 %}<div class="chart-container"><img src="data:image/png;base64,{{ results.chart_base64 }}"></div>{% endif %}
        <table>
            <thead><tr><th>Service</th><th>INR</th><th>USD</th></tr></thead>
            <tbody>{% for i in results.report_data %}<tr><td>{{ i.Service }}</td><td>{{ i['Cost (INR)'] }}</td><td>{{ i['Cost (USD)'] }}</td></tr>{% endfor %}</tbody>
        </table>
        <div style="text-align: center; margin-top: 20px;">
            <form action="/download" method="POST" target="_blank">
                <input type="hidden" name="report_data_json" value="{{ report_data_json }}">
                <input type="hidden" name="start_date" value="{{ results.start_date }}">
                <input type="hidden" name="end_date" value="{{ results.end_date }}">
                <input type="hidden" name="total_in_rupees" value="{{ results.total_in_rupees }}">
                <select name="format" style="width: auto;"><option value="xlsx">Excel</option><option value="pdf">PDF</option></select>
                <input type="submit" value="Download" class="btn" style="width: auto; background: transparent; color: #064e3b; border: 2px solid #064e3b;">
            </form>
        </div>
    </div>
    {% endif %}
</div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results = {}; report_json = '[]'
    if request.method == 'POST':
        results = fetch_cost_data(request.form['key_id'], request.form['secret_key'], request.form['region'], request.form['start_date'], request.form['end_date'])
        if 'report_data' in results: report_json = json.dumps(results['report_data'])
    return render_template_string(HTML_TEMPLATE, results=results, report_data_json=report_json, TODAY=TODAY, FIRST_DAY_OF_MONTH=FIRST_DAY_OF_MONTH)

@app.route('/download', methods=['POST'])
def download():
    data = json.loads(request.form.get('report_data_json', '[]'))
    if not data: return "No data", 400
    fmt = request.form.get('format'); start = request.form.get('start_date'); end = request.form.get('end_date'); tot = request.form.get('total_in_rupees')
    fname = f"AWS_Cost_{start}_{end}"
    if fmt == 'pdf':
        buf = generate_pdf(data, start, end, tot)
        return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=f'{fname}.pdf')
    else:
        buf = io.BytesIO(); pd.DataFrame(data).to_excel(buf, index=False, engine='openpyxl'); buf.seek(0)
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'{fname}.xlsx')

if __name__ == '__main__': app.run(debug=True, host='0.0.0.0')
"# AWS-Project" 
# 💰 AWS Cloud Cost Analyzer (Mint Edition)

A modern, real-time **AWS Cloud Cost Monitoring Tool** built with **Python (Flask)**. It fetches cost data directly from **AWS Cost Explorer**, visualizes it with charts, and sends **Email Alerts** via **AWS SNS**.

The application features a beautiful **Mint Green Glassmorphism UI** that is fully responsive.

**✨ Now available as a standalone Executable (.exe) for Windows! No Python installation required.**

## 📸 Screenshots

### 🔐 Input & Configuration
Enter your AWS Access Keys and select the Date Range securely to fetch the report.

<img width="1890" height="947" alt="Input_form" src="https://github.com/user-attachments/assets/3c612413-147b-4b38-9b4c-be93c749f972" />

<img width="1892" height="942" alt="Dashboard" src="https://github.com/user-attachments/assets/db5f6cff-7835-4c93-8bb5-8af15f161114" />

---

## 🚀 Key Features

* **🎨 Modern UI:** Stunning *Mint Green & Pistachio Glassmorphism* design using CSS3.
* **📅 Dynamic Date Range:** Analyze costs for any specific date range (Start Date & End Date).
* **📊 Data Visualization:** Interactive **Bar Charts** generated to visualize service-wise spending.
* **📥 Report Generation:** Download detailed reports in **Excel (XLSX)** and **PDF** formats.
* **📧 Smart Email Alerts:** Integrated with **AWS SNS** to send email notifications for cost updates.
* **₹ Multi-Currency:** Automatically converts USD costs to **Indian Rupees (INR)**.
* **⚡ Standalone App:** Can be run as a simple `.exe` file without installing Python.

---

## 🛠️ Tech Stack & Tools Used

We used the following technologies to build this project:

### **Backend & Logic**
* **Python:** Core programming language.
* **Flask:** Micro-web framework for serving the application.
* **Boto3:** AWS SDK for Python to interact with Cost Explorer & SNS.

### **Data & Visualization**
* **Pandas:** For data manipulation and Excel report generation.
* **Matplotlib:** To generate cost breakdown bar charts.
* **OpenPyXL:** Engine to write Excel files.
* **FPDF:** Library to generate PDF reports.

### **Frontend**
* **HTML5 & CSS3:** Custom Glassmorphism design (No external CSS frameworks used).
* **Jinja2:** Templating engine to render dynamic data in HTML.

### **Deployment & Packaging**
* **PyInstaller:** Used to convert the Python script into a standalone Windows Executable (`.exe`).

---

## 🏃‍♂️ How to Run (Two Ways)

### Option 1: Run using Executable (.exe) - *Easiest*
1.  Download the `cost_analyzer.exe` file from the `dist` folder or Releases.
2.  Double-click the `.exe` file.
3.  A black terminal window will open (Do not close this, it is the server).
4.  Open your browser and go to: `http://127.0.0.1:5000`

### Option 2: Run using Python Code
1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/gowthamArajendran/AWS-Project.git](https://github.com/gowthamArajendran/AWS-Project.git)
    cd AWS-Project
    ```

2.  **Install Dependencies**
    ```bash
    pip install Flask boto3 matplotlib pandas fpdf openpyxl pyinstaller
    ```

3.  **Run the Application**
    ```bash
    python cost_analyzer.py
    ```

---

## ⚙️ AWS Configuration

To fetch data, you need an **AWS IAM User** with the following permissions:
* `ce:GetCostAndUsage` (To fetch cost data)
* `sns:Publish` (To send email alerts)

> **Note:** You can enter your **Access Key ID** and **Secret Access Key** directly in the Web App securely.

---

## 📸 Application Interface

### 🔐 Secure Login & Configuration
Enter your AWS credentials and select the date range to generate reports.

<img width="1890" height="947" alt="Input_form" src="https://github.com/user-attachments/assets/3c612413-147b-4b38-9b4c-be93c749f972" />

---

## 👤 Author

**Gowtham R**
* [LinkedIn](https://www.linkedin.com/in/gowthamrmca/)
* [GitHub](https://github.com/gowthamArajendran)

---
*Built for efficient Cloud Financial Management (FinOps).*





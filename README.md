# FinAssist – Finance Loan Management AI Chatbot

**Smart Loan Management | Financial Calculations | AI-Powered Assistance**

FinAssist is a full-stack finance loan management and customer tracking web application designed specifically for small finance businesses.

It simplifies financial operations by providing customer management, loan tracking, interest calculations, repayment schedule generation, payment recording, financial analytics, and an intelligent AI-powered finance chatbot.

---

## 🚀 Key Features

### 📊 1. Executive Dashboard
- Total customer statistics.
- Active loan tracking.
- Total amount lent and repaid.
- Outstanding loan balance.
- Expected interest.
- Today's collection statistics.

### 🤖 2. AI Finance Chatbot
- Natural language financial queries.
- OpenAI GPT-4o-mini integration.
- Database-backed customer and loan information.
- Financial calculation assistance.
- Internal fallback engine when OpenAI API access is unavailable.

**Example Questions:**
- How much does Ravi owe?
- Calculate ₹50,000 for 12 months at 2% interest.
- Show today's collections.

### 🧮 3. Loan Calculator
- Flat interest calculation.
- Reducing balance EMI calculation.
- Side-by-side interest comparison.
- Daily, weekly, and monthly payment frequencies.
- Detailed repayment schedule.

### 📅 4. Repayment Schedule Generator
- Automatic installment generation.
- Principal and interest breakdown.
- Due date tracking.
- Payment status monitoring.
- Pending, Paid, Partially Paid, and Overdue statuses.

### 👥 5. Customer Management
- Add, edit, and delete customers.
- Search customer records.
- View customer details.
- Track borrowing history.
- Monitor outstanding balances.

### 💰 6. Loan Management
- Issue new loans.
- Manage loan contracts.
- Track repayment progress.
- View repayment schedules.
- Monitor outstanding loan balances.

### 💳 7. Payment Management
- Record customer payments.
- Cash, UPI, and Bank Transfer support.
- Automatic repayment schedule allocation.
- Loan balance updates.
- Payment status tracking.

### 📈 8. Reports & Analytics
- Monthly collection trends.
- Loan portfolio analysis.
- Interactive Chart.js visualizations.
- CSV report export.
- Financial performance monitoring.

---

## 🛠️ Technology Stack

| Category | Technology |
|---|---|
| Frontend | HTML5, CSS3 |
| Programming Language | JavaScript ES6 |
| Backend | Python, Flask |
| API Support | Flask-CORS |
| Database | SQLite |
| AI Integration | OpenAI GPT-4o-mini |
| AI Fallback | Internal Financial Rule Engine |
| Data Visualization | Chart.js |
| Environment Configuration | python-dotenv |
| Testing | Python |
| Version Control | Git, GitHub |

---

## 📂 Project Structure

```text
FinAssist/
│
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── calculations.py
│   ├── chatbot.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── test_backend.py
│   └── test_http_endpoints.py
│
├── frontend/
│   ├── dashboard.html
│   ├── customers.html
│   ├── loans.html
│   ├── payments.html
│   ├── calculator.html
│   ├── reports.html
│   │
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       ├── app.js
│       ├── dashboard.js
│       ├── customers.js
│       ├── loans.js
│       ├── payments.js
│       ├── calculator.js
│       ├── chatbot.js
│       └── reports.js
│
├── .gitignore
├── README.md
└── package-lock.json
```

---

## ⚙️ Installation & Setup

Follow these steps to run FinAssist on your Windows computer.

### Prerequisites

- Python 3.x
- Git
- Visual Studio Code (recommended)
- Modern web browser

### Step 1: Clone the Repository

```powershell
git clone https://github.com/HarikrishnanS1713/FinAssist.git
```

### Step 2: Navigate to the Project

```powershell
cd FinAssist
```

### Step 3: Create a Virtual Environment

```powershell
python -m venv venv
```

### Step 4: Activate the Virtual Environment

```powershell
venv\Scripts\activate
```

### Step 5: Install Dependencies

```powershell
python -m pip install -r backend\requirements.txt
```

### Step 6: Configure Environment Variables

Create a `.env` file in the project root directory.

Use `backend/.env.example` as a reference.

Add your configuration:

```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_PORT=5000
SECRET_KEY=your_secure_random_secret_key
```

**Note:** An OpenAI API key is required for OpenAI-powered chatbot functionality. The internal fallback engine can handle supported queries when API access is unavailable.

Never upload your actual `.env` file or API credentials to GitHub.

### Step 7: Run the Application

```powershell
python backend\app.py
```

### Step 8: Open in Browser

Open your browser and visit:

http://127.0.0.1:5000

---

## 🧪 Testing

Run backend calculation and database tests:

```powershell
python backend\test_backend.py
```

For HTTP endpoint testing, start the Flask server in one terminal and execute the following command in another terminal:

```powershell
python backend\test_http_endpoints.py
```

---

## 🔐 Security

- Store API keys in environment variables.
- Never commit `.env` files.
- Use a secure Flask secret key.
- Avoid exposing real customer financial information.
- Configure appropriate authentication and authorization before production deployment.

---

## 🔮 Future Enhancements

- Advanced financial analytics.
- PDF report generation.
- Enhanced AI-powered financial insights.
- Role-based authentication.
- Cloud database integration.
- Automated payment reminders.
- Improved mobile responsiveness.
- Production deployment.

---

## 👨‍💻 Developer

**Harikrishnan S**

- GitHub: https://github.com/HarikrishnanS1713
- LinkedIn: https://www.linkedin.com/in/harikrishnans04/

**Project:** FinAssist – Finance Loan Management AI Chatbot

---

## 📄 License

No open-source license has currently been specified for this project. All rights are reserved by the project owner unless a license is added.

---

**FinAssist – Making Financial Management Smarter and Simpler.**
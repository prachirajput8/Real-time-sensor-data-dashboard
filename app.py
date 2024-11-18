from flask import Flask, jsonify, render_template, request, send_file,  redirect, url_for, session, flash
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
import openpyxl
import os
import secrets
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # 32-character hex string

secret_key = os.urandom(24)  # This generates a 24-byte random secret key

# Setup Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file("C:\\Users\\ASUS\\Downloads\\rpi4gspread-cb304c38261c.json", scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_ID = '1FeqD_rpgvpGU88SouXAlIGa1gYdykaGIGvi_Pb0y1JM'
SHEET_NAME = 'Sheet1'

USERNAME = "admin"
PASSWORD = "password"

def read_data():
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(SHEET_NAME)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df['Time stamp'] = pd.to_datetime(df['Time stamp'])
    return df


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('filter_by_date'))
        else:
            error = "Invalid username or password."
            return render_template('login.htm', error=error)
    return render_template('login.htm')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/download_excel', methods=['GET'])

def download_excel():
    try:
        df = read_data()  # Fetch data from Google Sheets
        output = BytesIO()  # In-memory file

        # Save DataFrame to Excel file in memory
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        output.seek(0)

        # Send the file as a downloadable attachment
        return send_file(
            output,
            as_attachment=True,
            download_name='data.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/filter_by_date', methods=['GET'])
def filter_by_date():
    date_str = request.args.get('date')
    df = read_data()

    if date_str:
        filter_date = pd.to_datetime(date_str).date()
    else:
        filter_date = datetime.today().date()

    filtered_data = df[df['Time stamp'].dt.date == filter_date]
    
    plt.figure(figsize=(14, 6))  # Increase width for horizontal layout

# Plot Temperature in the first subplot (first column)
    plt.subplot(1, 2, 1)  # (rows, columns, index)
    plt.plot(filtered_data['Time stamp'], filtered_data['Temperature '], label='Temperature', color='red')
    plt.xlabel('Time')
    plt.ylabel('Temperature')
    plt.title(f"Temperature Data on {filter_date}")
    plt.legend()

    # Plot Humidity in the second subplot (second column)
    plt.subplot(1, 2, 2)  # (rows, columns, index)
    plt.plot(filtered_data['Time stamp'], filtered_data['Humidity'], label='Humidity', color='blue')
    plt.xlabel('Time')
    plt.ylabel('Humidity')
    plt.title(f"Humidity Data on {filter_date}")
    plt.legend()

    
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')

    return render_template(
        'dashboard1.htm',
        plot_url=f"data:image/png;base64,{plot_url}",
        filtered_data=filtered_data.to_dict(orient='records')
    )
@app.route('/data_page', methods=['GET'])
def data_page():
    # Get the date parameter from the URL (if provided), otherwise use today's date
    date_str = request.args.get('date')
    df = read_data()  # Fetch data from Google Sheets
    
    # If a date is provided, filter the data based on that date
    if date_str:
        filter_date = pd.to_datetime(date_str).date()
    else:
        filter_date = datetime.today().date()
    
    # Filter the data for the selected date or today's date
    filtered_data = df[df['Time stamp'].dt.date == filter_date]

    # Pass the filtered data to the HTML template
    return render_template('viewdata.htm', data=filtered_data.to_dict(orient='records'), filter_date=filter_date)


@app.route('/display', methods=['GET'])
def display_page():
    # Load the full data
    df=read_data()
    
    # Select only the top 10 rows
    top_10_data = df.head(10)
    
    # Pass the top 10 data to the HTML template
    return render_template('dashboard1.htm', data=top_10_data.to_dict(orient='records'))
@app.route('/')
def home():
    return render_template('login.htm')
    return render_template('dashboard1.htm')
    return render_template('viewdata.htm')
    



if __name__ == '__main__':
    app.run(debug=True)







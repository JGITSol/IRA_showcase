import sqlite3
import os
import datetime

class Database:
    def __init__(self, db_name='insurance_predictions.db'):
        """Initialize database connection and create table if it doesn't exist."""
        # Create the data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
        
        self.conn = sqlite3.connect(f'data/{db_name}')
        self.cursor = self.conn.cursor()
        
        # Create table if it doesn't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER,
            gender TEXT,
            bmi REAL,
            children INTEGER,
            smoker TEXT,
            region TEXT,
            predicted_charges REAL,
            prediction_date TEXT
        )
        ''')
        self.conn.commit()
    
    def add_prediction(self, age, gender, bmi, children, smoker, region, predicted_charges):
        """Add a new prediction to the database."""
        prediction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute('''
        INSERT INTO predictions (age, gender, bmi, children, smoker, region, predicted_charges, prediction_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (age, gender, bmi, children, smoker, region, predicted_charges, prediction_date))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_predictions(self):
        """Retrieve all predictions from the database."""
        self.cursor.execute('SELECT * FROM predictions ORDER BY prediction_date DESC')
        columns = [desc[0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        # Convert to list of dictionaries
        predictions = []
        for row in results:
            predictions.append(dict(zip(columns, row)))
        
        return predictions
    
    def get_prediction_by_id(self, prediction_id):
        """Retrieve a specific prediction by ID."""
        self.cursor.execute('SELECT * FROM predictions WHERE id = ?', (prediction_id,))
        columns = [desc[0] for desc in self.cursor.description]
        result = self.cursor.fetchone()
        
        if result:
            return dict(zip(columns, result))
        return None
    
    def update_prediction(self, prediction_id, age, gender, bmi, children, smoker, region, predicted_charges):
        """Update an existing prediction."""
        prediction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute('''
        UPDATE predictions
        SET age = ?, gender = ?, bmi = ?, children = ?, smoker = ?, region = ?, 
            predicted_charges = ?, prediction_date = ?
        WHERE id = ?
        ''', (age, gender, bmi, children, smoker, region, predicted_charges, prediction_date, prediction_id))
        
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_prediction(self, prediction_id):
        """Delete a prediction from the database."""
        self.cursor.execute('DELETE FROM predictions WHERE id = ?', (prediction_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
import datetime
import os
import sqlite3
import threading
from typing import Optional

class Database:
    def __init__(self, db_name='insurance_predictions.db'):
        """Initialize database connection and create table if it doesn't exist."""
        # Create the data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
        
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(f'data/{db_name}', check_same_thread=False)

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age INTEGER,
                gender TEXT,
                bmi REAL,
                children INTEGER,
                smoker TEXT,
                region TEXT,
                predicted_charges REAL,
                risk_score REAL,
                confidence REAL,
                ci_lower REAL,
                ci_upper REAL,
                prediction_date TEXT
            )
            ''')
            self.conn.commit()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Ensure legacy databases gain the newer analytical columns."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('PRAGMA table_info(predictions)')
            existing_columns = {row[1] for row in cursor.fetchall()}
            desired_columns = {
                "risk_score": "REAL",
                "confidence": "REAL",
                "ci_lower": "REAL",
                "ci_upper": "REAL",
            }

            for column, column_type in desired_columns.items():
                if column not in existing_columns:
                    cursor.execute(f"ALTER TABLE predictions ADD COLUMN {column} {column_type}")

            self.conn.commit()
    
    def add_prediction(
        self,
        age: int,
        gender: str,
        bmi: float,
        children: int,
        smoker: str,
        region: str,
        predicted_charges: float,
        risk_score: Optional[float] = None,
        confidence: Optional[float] = None,
        ci_lower: Optional[float] = None,
        ci_upper: Optional[float] = None,
    ) -> Optional[int]:
        """Add a new prediction to the database."""
        prediction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
            INSERT INTO predictions (
                age, gender, bmi, children, smoker, region,
                predicted_charges, risk_score, confidence, ci_lower, ci_upper, prediction_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
                (
                    age,
                    gender,
                    bmi,
                    children,
                    smoker,
                    region,
                    predicted_charges,
                    risk_score,
                    confidence,
                    ci_lower,
                    ci_upper,
                    prediction_date,
                ),
            )
            self.conn.commit()
            return cursor.lastrowid
    
    def get_all_predictions(self):
        """Retrieve all predictions from the database."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM predictions ORDER BY prediction_date DESC')
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            # Convert to list of dictionaries
            predictions = [dict(zip(columns, row)) for row in results]
            return predictions
    
    def get_prediction_by_id(self, prediction_id):
        """Retrieve a specific prediction by ID."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM predictions WHERE id = ?', (prediction_id,))
            columns = [desc[0] for desc in cursor.description]
            result = cursor.fetchone()

            if result:
                return dict(zip(columns, result))
            return None
    
    def update_prediction(self, prediction_id, age, gender, bmi, children, smoker, region, predicted_charges):
        """Update an existing prediction."""
        prediction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE predictions
            SET age = ?, gender = ?, bmi = ?, children = ?, smoker = ?, region = ?, 
                predicted_charges = ?, prediction_date = ?
            WHERE id = ?
            ''', (age, gender, bmi, children, smoker, region, predicted_charges, prediction_date, prediction_id))

            self.conn.commit()
            return cursor.rowcount > 0
    
    def delete_prediction(self, prediction_id):
        """Delete a prediction from the database."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM predictions WHERE id = ?', (prediction_id,))
            self.conn.commit()
            return cursor.rowcount > 0
    
    def close(self):
        """Close the database connection."""
        with self._lock:
            self.conn.close()
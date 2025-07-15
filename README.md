# Insurance Risk Analyzer (IRA) Showcase

A production-ready FastAPI application for analyzing insurance risk and predicting insurance charges based on demographic and health data. This application provides a robust API for insurance risk assessment with features for user management, prediction history, and risk analysis.

## 🚀 Features

- **Predictive Analytics**: Machine learning models for insurance charge prediction
- **User Management**: Secure authentication and authorization with JWT
- **RESTful API**: Fully documented endpoints with OpenAPI and Swagger UI
- **Asynchronous Processing**: High-performance async database operations
- **Containerized**: Ready for Docker and Kubernetes deployment
- **Scalable**: Designed for horizontal scaling
- **Monitoring**: Built-in health checks and metrics
- **CI/CD Ready**: GitHub Actions workflow for testing and deployment

## 🛠️ Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 6+ (for caching and async tasks)
- Docker 20.10+ (for containerized deployment)
- Docker Compose 2.0+
- Make (optional, for convenience commands)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

The easiest way to get started is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/yourusername/ira-showcase.git
cd ira-showcase

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Start the application
make up
```

This will start all services:

- FastAPI application: `http://localhost:8000`
- PostgreSQL database
- PgAdmin: `http://localhost:5050`
- Redis

### Manual Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ira-showcase.git
   cd ira-showcase
   ```

2. **Set up Python environment**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up the database**
   ```bash
   # Start PostgreSQL and Redis services
   docker-compose up -d postgres redis
   
   # Run database migrations
   make db-upgrade
   
   # Seed initial data (optional)
   make db-seed
   ```

5. **Run the application**
   ```bash
   # Development mode with hot reload
   make dev
   
   # Production mode
   make start
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example` and configure the following:

```env
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=info
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DB_DRIVER=postgresql+asyncpg
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=insurance_risk
POOL_SIZE=5
POOL_OVERFLOW=10
POOL_RECYCLE=3600

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# CORS
FRONTEND_URL=http://localhost:3000

# ML Model
MODEL_PATH=./models/insurance_risk_model.pkl
```

### Database Migrations

This project uses Alembic for database migrations:

```bash
# Create a new migration
make db-revision message="your migration message"

# Apply all pending migrations
make db-upgrade

# Revert the last migration
make db-downgrade

# Show current migration status
make db-current
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/path/to/test_file.py -v
```

## 🐳 Deployment

### Production Deployment

1. Update the `.env` file with production settings
2. Build and start the production stack:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```

### Kubernetes

For Kubernetes deployment, see the `k8s/` directory for example manifests.

## 📚 API Documentation

Once the application is running, you can access:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- SQLAlchemy for the ORM
- Pydantic for data validation
- All other open-source libraries used in this project

Start the Streamlit application:

```
streamlit run app.py
```

This will launch the application in your default web browser at `http://localhost:8501`.

### Making Predictions

1. Navigate to the "Predict" tab
2. Enter your information:
   - Age
   - Gender
   - BMI (Body Mass Index)
   - Number of children
   - Smoker status
   - Region
3. Click "Calculate Risk" to see your prediction

### Viewing History

Navigate to the "History" tab to view all previous predictions. You can:
- View details of any prediction
- Load a previous prediction for editing
- Delete predictions from the database

### Exploring Insights

Navigate to the "Insights" tab to:
- View feature importance charts
- Compare example predictions for different profiles

## Running Tests

The application includes comprehensive tests to ensure functionality:

```
python run_tests.py
```

Or run individual test modules:

```
python -m unittest tests.test_database
python -m unittest tests.test_model
python -m unittest tests.test_utils
```

## API Documentation

### Database Module

```python
from database import Database

# Initialize database
db = Database(db_name='insurance_predictions.db')

# Add a prediction
prediction_id = db.add_prediction(age, gender, bmi, children, smoker, region, predicted_charges)

# Get all predictions
predictions = db.get_all_predictions()

# Get prediction by ID
prediction = db.get_prediction_by_id(prediction_id)

# Update prediction
success = db.update_prediction(prediction_id, age, gender, bmi, children, smoker, region, predicted_charges)

# Delete prediction
success = db.delete_prediction(prediction_id)

# Close database connection
db.close()
```

### Model Module

```python
from model import train_model

# Train and save the model
model = train_model()
```

### Utils Module

```python
from utils import (
    load_model, predict_insurance_charges, generate_risk_score,
    plot_risk_gauge, plot_feature_importance, plot_prediction_comparison
)

# Load the trained model
model = load_model()

# Make a prediction
prediction = predict_insurance_charges(model, age, gender, bmi, children, smoker, region)

# Generate risk score (1-10)
risk_score = generate_risk_score(prediction, max_charge=50000)

# Create visualizations
risk_gauge_fig = plot_risk_gauge(risk_score)
feature_importance_fig = plot_feature_importance(model)
comparison_fig = plot_prediction_comparison(prediction, avg_charges)
```

## Project Structure

```
insurance-risk-predictor/
├── app.py                  # Main Streamlit application
├── database.py             # Database operations
├── model.py                # Model training and creation
├── utils.py                # Utility functions and visualizations
├── requirements.txt        # Project dependencies
├── README.md               # Project documentation
├── run_tests.py            # Test runner script
├── data/                   # Data directory
│   ├── insurance_data.csv  # Sample data
│   └── insurance_predictions.db  # SQLite database
├── models/                 # Model directory
│   └── insurance_model.pkl  # Trained model
└── tests/                  # Test directory
    ├── __init__.py         # Makes tests a package
    ├── test_database.py    # Database tests
    ├── test_model.py       # Model tests
    └── test_utils.py       # Utility tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- This project uses Streamlit for the web interface
- Machine learning models are built with scikit-learn
- Visualizations use Matplotlib and Seaborn
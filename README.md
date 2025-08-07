# Chip Testing Hourly Rate Quotation System

A full-stack web application for automatically calculating chip testing hourly rates based on selected equipment, configurations, and resources.

## Features

- Machine selection with different capabilities and rates
- Configuration options with additional costs
- Card type selection for specific testing needs
- Auxiliary equipment options
- Personnel allocation with different skill levels
- Real-time quotation calculation

## Technology Stack

### Backend
- FastAPI (Python)
- PostgreSQL (can use SQLite for development)
- SQLAlchemy ORM

### Frontend
- React.js (TypeScript)
- Ant Design
- Axios for API requests

## Project Structure
chip-quotation-system/ 
├── backend/ # FastAPI backend 
�?├── app/ # Application source code 
�?�?├── api/ # API endpoints 
�?�?├── models.py # Database models 
�?�?├── schemas.py # Pydantic schemas 
�?�?├── crud.py # Database operations 
�?�?├── database.py # Database configuration 
�?�?└── main.py # FastAPI application 
�?├── requirements.txt # Python dependencies 
�?└── init_data.py # Sample data initialization 
├── frontend/ # React frontend 
�?└── chip-quotation-frontend/ 
├── start_backend.ps1 # Backend startup script 
├── start_frontend.ps1 # Frontend startup script 
└── README.md


## Getting Started

### Prerequisites

- Python 3.7+
- Node.js 14+
- PostgreSQL (optional, can use SQLite for development)

### Installation

1. Clone or create the project:
   `ash
   # If you're reading this, you've already done this step


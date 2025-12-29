# GEMINI.md - Project Overview

## Project Overview

This is a **Chip Quotation System** designed to automate the process of generating quotes for chip testing. It features a web-based interface for users to input specifications and receive a calculated quote. The system also includes a robust approval workflow with support for both internal and WeCom (Enterprise WeChat) notifications and approvals.

The project is a full-stack application with a clear separation between the frontend and backend:

- **Frontend:** A modern, responsive web interface built with **React** and **TypeScript**. It utilizes the **Ant Design** component library for a consistent and professional user experience.
- **Backend:** A powerful and efficient API server built with **Python** and the **FastAPI** framework. It uses **SQLAlchemy** for database interactions, supporting **PostgreSQL** in production and **SQLite** for development.
- **Database:** The system is designed to work with **PostgreSQL** in a production environment, ensuring data integrity and scalability. For ease of development, it can also run with **SQLite**.

## Building and Running

### Backend

To run the backend server for development, follow these steps:

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the development server:**
    ```bash
    python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    ```
    The `--reload` flag enables hot-reloading, so the server will automatically restart when code changes are detected.

### Frontend

To run the frontend application for development, follow these steps:

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend/chip-quotation-frontend
    ```

2.  **Install the required Node.js packages:**
    ```bash
    npm install
    ```

3.  **Run the development server:**
    ```bash
    npm start
    ```
    This will start the React development server, and the application will be accessible at `http://localhost:3000` in your web browser.

## Development Conventions

Based on the project structure and code, the following development conventions are in place:

- **API Versioning:** The backend API is versioned, with the current version being `v1` and `v2`. New API endpoints should be added to the appropriate versioned router.
- **Clear Separation of Concerns:** The project maintains a strict separation between the frontend and backend codebases. All communication between the two should be through the defined API endpoints.
- **Styling:** The frontend uses **Ant Design** for UI components. It is recommended to use Ant Design components whenever possible to maintain a consistent look and feel.
- **Code Formatting:** While no explicit formatting rules are defined, it is recommended to follow standard Python (PEP 8) and TypeScript/React style guides to maintain code quality and readability.
- **Testing:** The project includes a `test` script in the frontend's `package.json`, suggesting that tests are written using `react-scripts`. It is recommended to write unit and integration tests for new features and bug fixes.

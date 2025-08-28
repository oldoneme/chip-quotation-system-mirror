# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

⚠️ **IMPORTANT**: Before making ANY changes, you MUST read and follow [CLAUDE_WORKFLOW.md](./CLAUDE_WORKFLOW.md) for mandatory workflow checks and safety rules.

## Project Overview

Chip Testing Hourly Rate Quotation System (芯片测试报价系统) - A full-stack web application for calculating chip testing quotations based on equipment selection, configurations, and resources. The system supports multiple quotation types and integrates with WeChat Work (企业微信) for authentication.

## Common Commands

### Backend Development
```bash
# Start backend (from backend/ directory)
cd backend
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Install dependencies
pip install -r requirements.txt

# Database operations
python3 init_data.py              # Initialize sample data
python3 check_db_content.py       # Check database content
python3 view_db_content.py        # View all database tables
```

### Frontend Development  
```bash
# Start frontend (from frontend/chip-quotation-frontend/)
cd frontend/chip-quotation-frontend
npm start                         # Development server
npm run build                     # Production build
npm test                          # Run tests

# Clear React cache for troubleshooting
rm -rf node_modules/.cache && rm -rf build && npm start
```

### Git Workflow
Current working branch: `feature/quote-wecom-usermanagement`
Main branch: `main`

## Architecture Overview

### Backend (FastAPI + SQLAlchemy)
- **FastAPI**: REST API server with automatic OpenAPI documentation
- **Database**: SQLite (development) with SQLAlchemy ORM
- **Authentication**: WeChat Work (企业微信) OAuth integration with session management
- **Models**: Hierarchical equipment structure (MachineTypes → Suppliers → Machines → Configurations/CardConfigs)

Key Components:
- `app/main.py`: FastAPI app with WeChat Work cache busting for WebView
- `app/models.py`: Database models with relationships
- `app/api/v1/`: API endpoints organized by resource
- `app/wecom_auth.py`: WeChat Work OAuth authentication
- `app/middleware/`: Custom middleware for permissions and confirmations

### Frontend (React + Ant Design)
- **React Router**: Multi-page navigation with state persistence
- **Ant Design**: UI component library
- **Context API**: Authentication and global state management
- **Session Storage**: Form state persistence across page navigation

Key Components:
- `src/contexts/AuthContext.js`: WeChat Work authentication context
- `src/pages/`: Quote type pages with state preservation pattern
- `src/services/`: API service layer with axios
- `src/components/CommonComponents.js`: Reusable UI components

### Quote Types Structure
The system supports 6 main quotation types:

1. **询价报价** (InquiryQuote): Initial inquiry pricing
2. **工装夹具报价** (ToolingQuote): Tooling and fixture pricing  
3. **工程机时报价** (EngineeringQuote): Engineering hourly rate
4. **量产机时报价** (MassProductionQuote): Mass production hourly rate
5. **量产工序报价** (ProcessQuote): Production process pricing
6. **综合报价** (ComprehensiveQuote): Comprehensive flexible pricing

### State Management Pattern
Quote pages use consistent state preservation:
- `isMounted` pattern prevents premature state saving
- `sessionStorage` for form data persistence
- Navigation with `fromResultPage` flag for state restoration
- Unified currency support: CNY and USD only

### Database Schema
Hierarchical equipment structure:
```
MachineType (测试机/分选机/编带机)
  └── Supplier (供应商)
      └── Machine (具体设备型号)
          ├── Configuration (配置选项)
          └── CardConfig (板卡配置)
```

### WeChat Work Integration
- OAuth authentication flow with corp_id/agent_id
- WebView cache busting with version-based URLs
- Session management with enterprise user data
- Permission-based UI access control

## Currency and Pricing
- Supported currencies: CNY (人民币), USD (美元)
- Exchange rate handling for cross-currency calculations
- Discount rates and markup factors per machine
- Unit price storage in database as integers (divide by 10000 for display)

## Development Notes

### State Persistence
All quote pages implement the same pattern:
1. Data fetching in useEffect with dependency on `location.state?.fromResultPage`
2. Set `isMounted = true` after data loading
3. Conditional sessionStorage saving only when mounted and not from result page
4. State restoration when `fromResultPage` is true

### API Proxy Configuration
Frontend development uses proxy: `"http://127.0.0.1:8000"` in package.json for API calls.

### Authentication Flow
1. WeChat Work OAuth → `/auth/callback`
2. User session creation with enterprise user data
3. Frontend AuthContext manages user state
4. Permission-based feature access (admin/super_admin roles)

### Cache Management
Enterprise WeChat WebView requires special cache handling:
- Version-based URL routing with APP_VERSION
- Clear-Site-Data headers for cache busting
- Static file serving with versioned paths

### Testing and Debugging
- `backend/simple_test.py`: Basic API testing
- `backend/check_*.py`: Database content verification scripts
- Frontend React DevTools for component debugging
- Browser cache clearing may be needed for WeChat Work WebView
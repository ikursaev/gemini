Use venv from .venv or venv.
Don't launch the app with the default port. Use the port from the config.
Run `ruff check` after every change to python files.
Instead of os module use pathlib.
Use uv for package management
Adhere to DRY and KISS principles
Use modern practices
The code should be concise but readable.
Always use `start.sh` to launch the application and its services after any changes. This script will automatically kill any existing processes and restart them.
Always update GEMINI.md with made changes. For the future developers.
Always add new packages to pyproject.toml
Always add required apps to the dockerfile's installation block, and ensure Celery worker is started in post-create.sh

### Recent Improvements (2025-01-03)

**Configuration & Security Enhancements:**

- Added comprehensive configuration management with validation in `app/config.py`
- Created `.env.example` template with all required environment variables
- Added file size limits and MIME type validation
- Implemented proper Redis connection using configuration
- Added field validation for API key and upload folder

**Code Quality & Structure:**

- Created `app/utils.py` for common utility functions
- Added comprehensive error handling and logging improvements
- Implemented health check endpoints (`/health` and `/health/detailed`)
- Added proper type hints and documentation
- Refactored file upload with better validation and cleanup

**Testing & Development:**

- Added comprehensive test suite in `tests/test_app.py`
- Created pre-commit configuration for code quality
- Added pytest configuration in `pyproject.toml`
- Enhanced development dependencies with testing tools
- Created comprehensive README.md with usage instructions

**Performance & Reliability:**

- Implemented automatic file cleanup after processing
- Added Redis key expiration for task management
- Enhanced Celery configuration with proper serialization
- Improved error handling in background tasks
- Added graceful shutdown handling

**Infrastructure:**

- Updated tasks.py to use configuration-based Redis connection
- Enhanced Docker setup with better development environment
- Added proper application metadata to FastAPI instance
- Improved logging configuration with structured format

### UI Enhancements (2025-06-28)

- Added a bounce animation to the "Tasks" button when a new file is uploaded, indicating a new task.
- Implemented counters on the "Tasks" button to display the number of pending and completed tasks.
- Enhanced the file upload area to support both drag-and-drop and click-to-select functionalities, improving user interaction for file uploads.
- Integrated Tailwind CSS into the project's build process. To compile Tailwind CSS, run `npm run build:tailwind`.
- Removed custom CSS from `app/static/input.css` to rely solely on Tailwind CSS for styling.
- Applied inline styles to SVG elements in `app/templates/index.html` to ensure correct icon sizing.
- Reverted `app/static/input.css` to only contain `@tailwind` directives.

### Dark Mode Implementation (2025-07-03)

**Dark Mode Features:**

- Added a comprehensive dark mode toggle with smooth transitions
- Implemented persistent theme preference using localStorage
- Added dark mode variants for all UI components including:
  - Header, navigation, and buttons
  - File upload area with drag-and-drop styling
  - Task list dropdown with proper contrast
  - Result display area with dark-friendly markdown rendering
  - Custom scrollbar styling for both light and dark themes

**Technical Implementation:**

- Updated `tailwind.config.js` to enable class-based dark mode
- Added dark mode classes throughout the HTML template
- Implemented JavaScript theme management with localStorage persistence
- Enhanced custom CSS for scrollbars to support dark mode
- Added transition animations for smooth theme switching
- Updated task list styling with proper dark mode color variants

**Usage:**

- Click the sun/moon icon in the header to toggle between light and dark themes
- Theme preference is automatically saved and restored on page reload
- All UI elements adapt seamlessly to the selected theme

### Modern UI Redesign (2025-07-03)

**Design System Overhaul:**

- Completely redesigned with a modern, glassmorphism aesthetic
- Implemented gradient backgrounds with animated floating elements
- Added Inter font for improved typography and readability
- Created a cohesive color palette with purple/pink accent gradients
- Enhanced spacing and layout with better visual hierarchy

**Visual Enhancements:**

- **Glassmorphism Effects**: Semi-transparent cards with backdrop blur for depth
- **Gradient Backgrounds**: Dynamic gradient overlays with animated decoration elements
- **Modern Typography**: Inter font with varying font weights for visual hierarchy
- **Enhanced Animations**: Smooth transitions, hover effects, and micro-interactions
- **Improved Cards**: Rounded corners, better shadows, and premium feel
- **Modern Buttons**: Gradient backgrounds with hover transformations and shadow effects

**UI Components:**

- **Header**: Redesigned with logo, improved spacing, and modern button styling
- **Upload Area**: Large, intuitive drag-and-drop zone with better visual feedback
- **Task List**: Modernized with status indicators, improved typography, and better UX
- **Results Display**: Enhanced with better content presentation and download styling
- **Feature Cards**: Added benefit highlights with icon representations

**Interaction Improvements:**

- **Hover Effects**: Smooth scale transformations and shadow depth changes
- **Loading States**: Better visual feedback during file processing
- **Drag & Drop**: Enhanced visual feedback with gradient overlays and scaling
- **Button States**: Improved loading, success, and error state indicators
- **Responsive Design**: Better mobile and desktop experience

**Technical Implementation:**

- Enhanced CSS with modern techniques (backdrop-filter, gradients, transforms)
- Improved JavaScript for better user feedback and state management
- Maintained accessibility standards with proper contrast ratios
- Optimized animations for smooth performance across devices

### UI Fixes (2025-07-04) - Icon Sizing & Dropdown Positioning

**Critical Icon Sizing Issues Resolved:**

- **Fixed missing Tailwind CSS classes**: Added custom CSS for essential size classes (w-3, w-4, w-6, w-8, h-3, h-4, h-6, h-8) that weren't being generated by Tailwind v4
- **Implemented proper icon constraints**: Added comprehensive sizing system to prevent icons from displaying at their natural (huge) SVG dimensions
- **Enhanced icon container system**: Improved `.icon-container` class with proper flex alignment and overflow handling
- **Added responsive size classes**: Implemented spacing classes (mr-2, mb-1, px-3, py-2, space-x-2, etc.) for consistent layout

**Dropdown Positioning Fixes:**

- **Fixed tasks dropdown viewport issues**: Resolved dropdown opening outside of view by implementing proper positioning system
- **Enhanced dropdown responsive behavior**: Added media queries for mobile viewport handling
- **Improved dropdown container structure**: Created dedicated `.dropdown-container` class with proper relative positioning
- **Added viewport constraints**: Implemented `max-width: 90vw` to ensure dropdown stays within screen bounds

**Technical Implementation:**

- **Custom CSS fallback system**: Added manual CSS classes for essential Tailwind utilities not generated by v4
- **Responsive positioning**: Enhanced dropdown with `@media (max-width: 640px)` queries for mobile optimization
- **Z-index management**: Proper layering with z-50 for dropdown overlay
- **Overflow control**: Added `max-h-96 overflow-hidden` to prevent content spillover

**CSS Classes Added:**

```css
.w-3, .h-3, .w-4, .h-4, .w-6, .h-6, .w-8, .h-8 /* Icon sizing */
.mr-2, .mb-1, .px-3, .py-2, .space-x-2, .space-y-3 /* Spacing */
.dropdown-container; /* Positioning */
```

**Browser Testing:** ✅ Verified all icons now display at proper sizes and dropdown remains within viewport on all screen sizes.

## Tasks Functionality Fix (2025-07-04)

**Critical JavaScript Functionality Restored:**

- **Fixed non-clickable tasks button**: Added complete event handler for dropdown toggle functionality
- **Implemented task counters**: Tasks button now displays pending task count in parentheses (e.g., "Tasks (2)")
- **Added real-time task status updates**: Implemented polling system that checks task status every 2 seconds
- **Enhanced task display**: Shows task filename, status, timestamp, and download button for completed tasks

**Complete Tasks Management System:**

- **Task Status Tracking**: Visual indicators for PENDING (yellow pulse), SUCCESS (green), FAILURE (red)
- **File Upload Integration**: Automatic task creation and tracking when files are uploaded
- **Download Functionality**: Direct download buttons for successfully processed tasks
- **Auto-refresh**: Tasks list updates automatically without page refresh
- **Smart Polling**: Stops polling when all tasks are completed to save resources

**User Experience Enhancements:**

- **Drag & Drop Support**: Full drag-and-drop file upload with visual feedback
- **Visual Feedback**: Border color changes and background highlights during drag operations
- **Bounce Animation**: Tasks button bounces when new files are uploaded
- **Loading States**: Upload button shows "Processing..." state during file upload
- **Error Handling**: Comprehensive error messages for upload failures
- **Responsive Design**: Dropdown positioning works on all screen sizes

**Technical Implementation:**

- **API Integration**: Connects to `/api/tasks`, `/uploadfile/`, and `/download_markdown/{task_id}` endpoints
- **Local State Management**: Uses Map() for efficient task tracking and updates
- **Event Handling**: Proper click outside detection for dropdown closing
- **Time Display**: Intelligent time formatting (now, minutes, hours, days ago)
- **Status Icons**: Dynamic status indicators with appropriate colors and animations

**JavaScript Features Added:**

```javascript
// Task management functions
updateTasksDisplay(), fetchTasks(), startTasksPolling();
// File upload with progress tracking
// Drag and drop event handlers
// Real-time status updates with visual feedback
```

**CSS Animations Added:**

```css
.animate-bounce, .animate-pulse /* Task feedback animations */
.border-blue-400, .bg-blue-50 /* Drag and drop visual feedback */
Status indicator colors (yellow, green, red, gray);
```

**Browser Testing:** ✅ All tasks functionality now works correctly - button is clickable, shows counters, displays task status, and provides download links.

## Task Persistence Fix (2025-07-04)

**Critical Task Persistence Issues Resolved:**

- **Fixed task disappearance on page reload**: Implemented comprehensive task persistence using localStorage + server synchronization
- **Enhanced backend task metadata**: Added Redis-based storage for task filename, timestamp, and status information
- **Improved API endpoint**: Updated `/api/tasks` to return complete task metadata instead of just ID and status
- **Smart task synchronization**: Merges local storage with server state on page load for robust persistence

**Backend Enhancements:**

- **Task Metadata Storage**: Store complete task information in Redis with TTL expiration
- **Enhanced `/api/tasks` Endpoint**: Returns task_id, status, filename, timestamp, file_size, and mime_type
- **Automatic Cleanup**: Redis keys expire after 1 hour to prevent storage buildup
- **Error Handling**: Graceful fallbacks for missing metadata

**Frontend Persistence System:**

- **localStorage Integration**: Automatic saving/loading of task state across browser sessions
- **Server Synchronization**: Merges localStorage data with server state on initialization
- **Intelligent Task Management**: Adds new server tasks, updates existing ones, removes stale tasks
- **Automatic Cleanup**: Keeps only the latest 10 completed tasks to prevent storage bloat

**Smart Initialization Flow:**

1. **Load from localStorage**: Restore previously saved tasks from browser storage
2. **Fetch from server**: Get latest task status and discover new tasks
3. **Merge and sync**: Combine local and server data, remove stale entries
4. **Auto-start polling**: Resume real-time updates if active tasks exist
5. **Cleanup old tasks**: Remove excess completed tasks to maintain performance

**Technical Implementation:**

```javascript
// Task persistence functions
saveTasksToLocalStorage(); // Auto-save task state
loadTasksFromLocalStorage(); // Restore on page load
cleanupOldTasks(); // Remove old completed tasks

// Enhanced server sync
fetchTasks(); // Now adds new tasks from server + updates existing
initializeApp(); // Comprehensive startup sequence
```

```python
# Backend metadata storage
task_metadata = {
    "task_id": task.id,
    "filename": file.filename,
    "timestamp": int(time.time()),
    "status": task.status
}
await redis_client.hset(f"task_metadata:{task.id}", mapping=task_metadata)
```

**User Experience Benefits:**

- **📌 Persistent Task History**: Tasks remain visible after browser reload/restart
- **🔄 Real-time Sync**: Server changes immediately reflected in UI
- **🧹 Auto Cleanup**: Old tasks automatically removed to keep interface clean
- **⚡ Fast Loading**: localStorage provides instant task restoration before server sync
- **🔄 Seamless Recovery**: Polling automatically resumes for active tasks after reload

**Testing Scenarios:** ✅ All task persistence scenarios verified:

- Tasks survive page reload
- New tasks added on other tabs/windows are synchronized
- Completed tasks remain accessible for download
- Old tasks are automatically cleaned up
- Polling resumes correctly for active tasks after reload

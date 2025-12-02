# Duplicate Photo Finder

A Python desktop application for finding and managing duplicate photos using perceptual hashing. Built with Tkinter, this tool helps users identify duplicate images across multiple directories, even when files have been renamed or slightly modified.

## Features

- **Perceptual Hashing**: Uses dHash (difference hash) algorithm to detect duplicate images even when they've been resized, compressed, or have minor modifications
- **Multi-Directory Scanning**: Scan multiple directories simultaneously for comprehensive duplicate detection
- **Graphical User Interface**: Intuitive Tkinter-based GUI with thumbnail previews and pagination
- **Batch Operations**: Efficient batch processing of photos with multiprocessing support for faster hashing
- **Smart Database Management**: SQLite database tracks photo metadata with automatic cleanup of stale entries
- **Selective Deletion**: Preview and selectively delete duplicate photos with confirmation dialogs
- **Pagination**: Navigate through large sets of duplicates with page-based browsing
- **Progress Tracking**: Real-time status updates during scanning and processing operations

## Technology Stack

- **Python 3.x**: Core language
- **Tkinter**: GUI framework
- **PIL/Pillow**: Image processing and thumbnail generation
- **ImageHash**: Perceptual hashing algorithms (dHash)
- **SQLite3**: Database for photo metadata storage
- **Multiprocessing**: Parallel image hashing for improved performance

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/duplicate-photo-finder.git
cd duplicate-photo-finder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. **Select Folders**: Click "Select Folders" to choose one or more directories to scan for duplicates

3. **Scan for Duplicates**: Click the "Scan" button to:
   - Find all photo files in the selected directories
   - Compute perceptual hashes for new photos
   - Update the database with photo metadata
   - Display duplicate groups

4. **Review Duplicates**: Browse through duplicate photo groups displayed as thumbnails. Each group shows all photos with the same hash value.

5. **Delete Photos**:
   - Click on thumbnails to select photos for deletion
   - Click "Delete" to remove selected photos from both the filesystem and database
   - Confirm deletion in the dialog that appears

6. **Navigate Pages**: Use "Prev Page" and "Next Page" buttons to browse through multiple pages of duplicate groups

## Project Structure

```
duplicate-photo-finder/
├── main.py              # Application entry point and orchestration
├── database.py          # SQLite database operations and query management
├── finder.py            # Photo file discovery and filesystem operations
├── hasher.py            # Image hashing functionality (dHash)
├── interface.py         # Tkinter GUI implementation
├── widgets.py           # Custom Tkinter widgets (scrollable frames, etc.)
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Architecture Highlights

- **Modular Design**: Clean separation of concerns with dedicated modules for database, file operations, hashing, and UI
- **Efficient Database Queries**: Optimized SQL queries with pagination support for handling large photo collections
- **Multiprocessing**: Parallel image hashing using ProcessPoolExecutor for improved performance on multi-core systems
- **Debouncing**: UI updates are debounced to prevent excessive redraws during rapid navigation
- **Memory Management**: Proper handling of image objects and GUI references to prevent memory leaks

## Database Schema

The application uses SQLite with a simple schema:

```sql
CREATE TABLE photos (
    filepath TEXT PRIMARY KEY,
    hash TEXT NOT NULL,
    lastseen DATETIME
);
```

- `filepath`: Unique file path (primary key)
- `hash`: Perceptual hash value (dHash string)
- `lastseen`: Timestamp of last scan, used for cleanup of deleted files

## Supported Image Formats

- PNG
- JPEG/JPG
- GIF
- BMP

## Performance Considerations

- **Batch Processing**: Photos are processed in batches of 50 to balance memory usage and performance
- **Incremental Updates**: Only new photos are hashed; existing photos have their timestamps updated
- **Stale Entry Cleanup**: Automatically removes database entries for files that no longer exist on disk
- **Multiprocessing**: Configurable worker processes (up to 8) for parallel hashing operations

## License

This project is open source and available for personal and educational use.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page or submit a pull request.

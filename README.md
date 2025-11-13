# Photo Duplicate Finder

A modern, beautiful application for finding and managing duplicate photos in your collection. Available in both Tkinter (classic) and Flet (modern) versions.

## Features

- 🔍 **Smart Duplicate Detection**: Uses MD5 hash comparison to find exact duplicates
- 🖼️ **Thumbnail Grid View**: View all duplicates in an organized grid layout
- 🗑️ **Easy Management**: Delete duplicates with a single click (with confirmation)
- 💾 **Caching System**: Remembers previously scanned files for faster subsequent scans
- 🎨 **Modern UI**: Beautiful Material Design interface (Flet version)
- 🖱️ **Click to Open**: Open full-size images in your default viewer

## Installation

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Modern Flet Version (Recommended)

```bash
python main_flet.py
```

### Classic Tkinter Version

```bash
python main.py
```

## How It Works

1. **Select Directory**: Choose a folder containing your photos
2. **Scan for Duplicates**: The app scans all images and computes their hashes
3. **View Results**: See how many duplicate groups were found
4. **Manage Duplicates**: Open the thumbnail viewer to see all duplicates grouped together
5. **Delete Duplicates**: Click the delete button on any photo to remove it permanently

## Features Comparison

### Flet Version (Modern)

- ✅ Beautiful Material Design interface
- ✅ Responsive and modern UI components
- ✅ Smooth animations and transitions
- ✅ Better visual hierarchy
- ✅ Cross-platform (can also run as web app)

### Tkinter Version (Classic)

- ✅ Lightweight and built-in with Python
- ✅ Simple and familiar interface
- ✅ No additional dependencies beyond Pillow

## Supported Image Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- BMP (.bmp)

## Cache File

The application creates a `_duplicate_photos_info` file in each scanned directory to cache hash information. This speeds up subsequent scans by only processing new or modified files.

## Development

### Project Structure

- `PhotoDuplicateFinder.py` - Core duplicate detection logic
- `PhotoDuplicateFinderAppFlet.py` - Flet-based main application
- `DuplicateThumbnailViewerFlet.py` - Flet-based thumbnail viewer
- `PhotoDuplicateFinderApp.py` - Tkinter-based main application
- `DuplicateThumbnailViewer.py` - Tkinter-based thumbnail viewer
- `main_flet.py` - Entry point for Flet version
- `main.py` - Entry point for Tkinter version

## Safety Features

- ✅ Confirmation dialog before deleting any photo
- ✅ Non-destructive scanning (read-only until you choose to delete)
- ✅ Clear visual feedback for all actions
- ✅ Error handling for missing or inaccessible files

## Requirements

- Python 3.7+
- Flet 0.24.0+ (for modern version)
- Pillow 10.0.0+

## License

This project is open source and available for personal and commercial use.


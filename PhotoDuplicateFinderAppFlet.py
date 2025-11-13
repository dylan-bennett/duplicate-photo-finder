import os
import threading

import flet as ft

from DuplicateThumbnailViewerFlet import DuplicateThumbnailViewerFlet
from PhotoDuplicateFinder import PhotoDuplicateFinder


class PhotoDuplicateFinderAppFlet:
    """
    Modern GUI application for finding and managing duplicate photos using Flet.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Photo Duplicate Finder"
        self.page.window_width = 700
        self.page.window_height = 600
        self.page.padding = 20
        self.page.theme_mode = ft.ThemeMode.LIGHT

        # Initialize the duplicate finder
        self.duplicate_finder = PhotoDuplicateFinder()

        # UI components
        self.dir_label = None
        self.scan_btn = None
        self.progress_bar = None
        self.progress_text = None
        self.results_text = None
        self.manage_btn = None

        # Create the main interface
        self.create_main_interface()

    def create_main_interface(self):
        """Create the main application interface."""
        # Title
        title = ft.Text(
            "Photo Duplicate Finder",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700,
        )

        subtitle = ft.Text(
            "Find and remove duplicate photos in your collection",
            size=14,
            color=ft.Colors.GREY_700,
        )

        # Directory selection section
        self.dir_label = ft.Text(
            "No directory selected",
            size=14,
            color=ft.Colors.GREY_500,
            weight=ft.FontWeight.W_400,
        )

        select_dir_btn = ft.ElevatedButton(
            "Select Folder",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self.select_directory,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.BLUE_600,
                    ft.ControlState.HOVERED: ft.Colors.BLUE_700,
                },
            ),
        )

        dir_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Select Photo Directory",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        self.dir_label,
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        select_dir_btn,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=20,
            ),
            elevation=2,
        )

        # Scan button
        self.scan_btn = ft.ElevatedButton(
            "Scan for Duplicates",
            icon=ft.Icons.SEARCH,
            on_click=self.start_scanning,
            disabled=True,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.GREEN_600,
                    ft.ControlState.HOVERED: ft.Colors.GREEN_700,
                },
            ),
        )

        # Progress section
        self.progress_text = ft.Text(
            "Ready to scan...",
            size=14,
            color=ft.Colors.GREY_700,
        )

        self.progress_bar = ft.ProgressBar(
            width=400,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100,
            visible=False,
        )

        progress_container = ft.Container(
            content=ft.Column(
                [self.progress_text, self.progress_bar],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=20,
        )

        # Results section
        self.results_text = ft.Text(
            "No scan performed yet",
            size=14,
            color=ft.Colors.GREY_500,
        )

        self.manage_btn = ft.ElevatedButton(
            "Manage Duplicates",
            icon=ft.Icons.PHOTO_LIBRARY,
            on_click=self.open_duplicate_viewer,
            disabled=True,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.ORANGE_600,
                    ft.ControlState.HOVERED: ft.Colors.ORANGE_700,
                },
            ),
        )

        results_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Results",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        self.results_text,
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        self.manage_btn,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=20,
            ),
            elevation=2,
        )

        # Add all components to the page
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        subtitle,
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        dir_card,
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        self.scan_btn,
                        progress_container,
                        results_card,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                expand=True,
            )
        )

    def select_directory(self, e):
        """Open folder selection dialog or show manual input for web."""
        # Check if we're running in web mode
        if self.page.platform_brightness is not None:  # Web mode
            # self.show_directory_input_dialog()
            self.show_file_picker_dialog()
        else:  # Desktop mode
            self.show_file_picker_dialog()

    def show_file_picker_dialog(self):
        """Show native file picker dialog (desktop only)."""
        def on_result(e: ft.FilePickerResultEvent):
            if e.path:
                self.set_directory(e.path)

        file_picker = ft.FilePicker(on_result=on_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.get_directory_path(
            dialog_title="Select folder to scan for duplicate photos"
        )

    def show_directory_input_dialog(self):
        """Show manual directory input dialog (web mode)."""
        def on_submit(e):
            if directory_input.value and directory_input.value.strip():
                directory_path = directory_input.value.strip()
                if os.path.isdir(directory_path):
                    self.set_directory(directory_path)
                    dialog.open = False
                    self.page.update()
                else:
                    error_text.value = f"Directory does not exist: {directory_path}"
                    error_text.visible = True
                    self.page.update()
            else:
                error_text.value = "Please enter a directory path"
                error_text.visible = True
                self.page.update()

        def on_cancel(e):
            dialog.open = False
            self.page.update()

        # Create dialog components
        directory_input = ft.TextField(
            label="Directory Path",
            hint_text="/home/username/Pictures",
            width=400,
            autofocus=True,
        )

        error_text = ft.Text(
            "",
            color=ft.Colors.RED_700,
            visible=False,
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Select Photo Directory"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Enter the full path to the directory containing your photos:",
                            size=14,
                            color=ft.Colors.GREY_700,
                        ),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        directory_input,
                        error_text,
                    ],
                    spacing=10,
                ),
                width=450,
                height=200,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel),
                ft.ElevatedButton("Select", on_click=on_submit),
            ],
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def set_directory(self, directory_path):
        """Set the directory and update UI."""
        self.duplicate_finder.directory_to_scan = directory_path
        self.duplicate_finder.cache_file = os.path.join(
            directory_path, self.duplicate_finder.cache_filename
        )

        # Update UI
        self.dir_label.value = directory_path
        self.dir_label.color = ft.Colors.BLACK
        self.scan_btn.disabled = False
        self.progress_text.value = "Ready to scan..."
        self.page.update()

    def start_scanning(self, e):
        """Start the duplicate scanning process in a separate thread."""
        if not self.duplicate_finder.directory_to_scan:
            self.show_dialog("Error", "Please select a directory first.")
            return

        # Disable button during scanning
        self.scan_btn.disabled = True

        # Start progress bar
        self.progress_bar.visible = True
        self.progress_text.value = "Scanning directory for images..."
        self.page.update()

        # Start scanning in a separate thread
        scan_thread = threading.Thread(target=self.scan_directory)
        scan_thread.daemon = True
        scan_thread.start()

    def scan_directory(self):
        """Perform the actual directory scanning."""
        try:
            # Load existing hash data if cache file exists
            if os.path.isfile(self.duplicate_finder.cache_file):
                self.update_progress("Loading existing cache...")
                self.duplicate_finder.read_cache_file()

            # Scan directory and compute hashes
            self.update_progress("Computing file hashes...")
            self.duplicate_finder.extract_file_hashes()

            # Write the data to the cache file
            self.duplicate_finder.write_cache_file()

            # Update UI with results
            self.scan_complete()

        except Exception as error:
            self.scan_error(str(error))

    def update_progress(self, message):
        """Update progress text from background thread."""
        self.progress_text.value = message
        self.page.update()

    def scan_complete(self):
        """Called when scanning is complete."""
        # Stop progress bar
        self.progress_bar.visible = False

        # Count duplicates
        num_duplicates = self.duplicate_finder.calculate_num_duplicates()
        total_files = len(self.duplicate_finder.cache_data["files"])

        if num_duplicates == 0:
            self.results_text.value = (
                f"Scan complete! No duplicates found in {total_files} files."
            )
            self.results_text.color = ft.Colors.GREEN_700
            self.manage_btn.disabled = True
        else:
            self.results_text.value = (
                f"Found {num_duplicates} groups of duplicates in {total_files} files."
            )
            self.results_text.color = ft.Colors.ORANGE_700
            self.manage_btn.disabled = False

        self.progress_text.value = "Scan complete!"
        self.scan_btn.disabled = False
        self.page.update()

    def scan_error(self, error_message):
        """Called when scanning encounters an error."""
        self.progress_bar.visible = False
        self.progress_text.value = "Scan failed!"
        self.scan_btn.disabled = False
        self.page.update()

        self.show_dialog(
            "Scan Error", f"An error occurred during scanning:\n{error_message}"
        )

    def show_dialog(self, title, message):
        """Show a dialog with a message."""

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=close_dialog),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def show_confirmation_dialog(self, title, message, on_confirm):
        """Show a confirmation dialog with Yes/No buttons."""

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def confirm_action(e):
            dialog.open = False
            self.page.update()
            on_confirm()

        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Yes", on_click=confirm_action),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def open_duplicate_viewer(self, e):
        """Open the duplicate thumbnail viewer in the main app."""
        self.show_duplicate_management_interface()

    def show_duplicate_management_interface(self):
        """Show the duplicate management interface in the main app."""
        # Clear the current page
        self.page.controls.clear()

        # Get duplicate entries
        duplicate_entries = self.duplicate_finder.get_duplicate_entries()

        if not duplicate_entries:
            self.show_no_duplicates_interface()
            return

        # Create back button
        back_btn = ft.ElevatedButton(
            "Back to Main",
            icon=ft.Icons.ARROW_BACK,
            on_click=self.back_to_main,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREY_600,
                color=ft.Colors.WHITE,
            ),
        )

        # Create title
        title = ft.Text(
            f"Manage {len(duplicate_entries)} Groups of Duplicates",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700,
        )

        instructions = ft.Text(
            "Click on images to view full size. Use delete buttons to remove unwanted duplicates.",
            size=14,
            color=ft.Colors.GREY_700,
        )

        # Create thumbnail grid
        thumbnail_grid = self.create_duplicate_thumbnail_grid(duplicate_entries)

        # Add everything to page
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        back_btn,
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        title,
                        instructions,
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        thumbnail_grid,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=20,
                expand=True,
            )
        )
        self.page.update()

    def show_no_duplicates_interface(self):
        """Show interface when no duplicates are found."""
        back_btn = ft.ElevatedButton(
            "Back to Main",
            icon=ft.Icons.ARROW_BACK,
            on_click=self.back_to_main,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREY_600,
                color=ft.Colors.WHITE,
            ),
        )

        no_duplicates_text = ft.Text(
            "🎉 No duplicates found!",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_700,
        )

        self.page.controls.clear()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        back_btn,
                        ft.Divider(height=50, color=ft.Colors.TRANSPARENT),
                        no_duplicates_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                expand=True,
            )
        )
        self.page.update()

    def back_to_main(self, e):
        """Return to the main interface."""
        self.page.controls.clear()
        self.create_main_interface()

    def create_duplicate_thumbnail_grid(self, duplicate_entries):
        """Create a thumbnail grid for duplicate photos."""
        import base64
        import io

        from PIL import Image

        grid_items = []

        for group_index, (file_hash, photo_files) in enumerate(duplicate_entries):
            current_row = []

            # Add group separator
            if group_index > 0:
                separator = ft.Divider(height=2, color=ft.Colors.BLUE_300)
                grid_items.append(ft.Container(separator, padding=ft.Padding(10, 5, 10, 5)))

            # Add group header
            group_header = ft.Text(
                f"Duplicate Group {group_index + 1} ({len(photo_files)} files)",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_700,
            )
            grid_items.append(ft.Container(group_header, padding=ft.Padding(10, 10, 10, 5)))

            # Add photos in this group
            for photo_path in photo_files:
                try:
                    # Create thumbnail
                    with Image.open(photo_path) as img:
                        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')

                        # Convert to base64
                        buffer = io.BytesIO()
                        img.save(buffer, format='JPEG')
                        img_data = base64.b64encode(buffer.getvalue()).decode()

                        # Create image widget
                        image_widget = ft.Image(
                            src_base64=img_data,
                            width=200,
                            height=200,
                            fit=ft.ImageFit.CONTAIN,
                            tooltip=photo_path,
                        )

                        # Create delete button
                        delete_btn = ft.IconButton(
                            icon=ft.Icons.DELETE,
                            tooltip="Delete this photo",
                            on_click=lambda e, path=photo_path:
                                self.show_confirmation_dialog(
                                    "Confirm Delete",
                                    f"Are you sure you want to delete "
                                    f"'{os.path.basename(path)}'?\n\n"
                                    f"This action cannot be undone.",
                                    lambda: self.delete_photo(path)
                                ),
                            icon_color=ft.Colors.RED_700,
                        )

                        # Create photo info
                        filename = os.path.basename(photo_path)
                        file_size = os.path.getsize(photo_path)
                        size_mb = file_size / (1024 * 1024)

                        info_text = ft.Text(
                            f"{filename}\n{size_mb:.2f} MB",
                            size=12,
                            color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER,
                        )

                        # Create card for this photo
                        photo_card = ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        image_widget,
                                        info_text,
                                        delete_btn,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=5,
                                ),
                                padding=10,
                            ),
                            elevation=2,
                        )

                        current_row.append(photo_card)

                except Exception as e:
                    # Handle image loading errors
                    error_card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Error loading image", color=ft.Colors.RED_700),
                                    ft.Text(os.path.basename(photo_path), size=12),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=10,
                        ),
                        elevation=2,
                    )
                    current_row.append(error_card)

            # Add the thumbnails to the grid
            grid_items.append(ft.Row(current_row, spacing=10, wrap=True))

        return ft.Column(
            grid_items,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

    def delete_photo(self, photo_path):
        """Delete a photo file."""
        try:
            if os.path.exists(photo_path):
                os.remove(photo_path)
                self.duplicate_finder.delete_file_from_cache(photo_path)

                # Refresh the duplicate management interface
                self.show_duplicate_management_interface()
            else:
                self.show_dialog("Error", "File not found")
        except Exception as e:
            self.show_dialog("Error", f"Failed to delete file: {str(e)}")


def main(page: ft.Page):
    """Main entry point for Flet app."""
    PhotoDuplicateFinderAppFlet(page)


if __name__ == "__main__":
    ft.app(target=main)


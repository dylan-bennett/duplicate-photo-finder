import base64
import io
import os
import subprocess

import flet as ft
from PIL import Image


class DuplicateThumbnailViewerFlet:
    """
    Modern GUI class for viewing and managing duplicate photos
    in a thumbnail grid using Flet.
    """

    def __init__(self, duplicate_finder):
        self.duplicate_finder = duplicate_finder

    def delete_photo_with_confirmation(self, photo_path, page, refresh_callback):
        """
        Deletes a photo file with confirmation dialog and removes it from the UI.

        Args:
            photo_path (str): Path to the photo file to delete
            page (ft.Page): The page to show dialogs on
            refresh_callback: Callback to refresh the view after deletion
        """
        filename = os.path.basename(photo_path)

        def confirm_delete(_):
            dialog.open = False
            page.update()
            try:
                # Delete the file from filesystem
                os.remove(photo_path)
                print(f"Successfully deleted: {filename}")

                # Update the duplicate finder's cache data
                self.update_cache_after_deletion(photo_path)

                # Refresh the view
                refresh_callback()

            except FileNotFoundError:
                self.show_error_dialog(page, "Error", f"File not found: {filename}")
            except OSError as e:
                self.show_error_dialog(page, "Error", f"Could not delete file: {e}")

        def cancel_delete(_):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Deletion", weight=ft.FontWeight.BOLD),
            content=ft.Text(
                f'Are you sure you want to delete "{filename}"?\n\n'
                f"This action cannot be undone."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton(
                    "Delete",
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.RED_600,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dialog
        dialog.open = True
        page.update()

    def update_cache_after_deletion(self, deleted_file_path):
        """Update the cache data after a file is deleted."""
        # Remove from files list
        if deleted_file_path in self.duplicate_finder.cache_data["files"]:
            self.duplicate_finder.cache_data["files"].remove(deleted_file_path)

        # Remove from hashes entries
        for file_hash, files in list(
            self.duplicate_finder.cache_data["hashes"].items()
        ):
            if deleted_file_path in files:
                files.remove(deleted_file_path)
                # If no files left for this hash, remove the hash entry
                if not files:
                    del self.duplicate_finder.cache_data["hashes"][file_hash]
                break

        # Write updated cache to file
        self.duplicate_finder.write_cache_file()

    def show_error_dialog(self, page, title, message):
        """Show an error dialog."""

        def close_dialog(_):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=close_dialog),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def show_duplicates_grid(self):
        """Show all duplicate groups in a thumbnail grid with separators."""
        # Get all duplicate groups
        duplicate_entries = [
            (hash_key, files)
            for hash_key, files in self.duplicate_finder.cache_data["hashes"].items()
            if len(files) > 1
        ]

        if not duplicate_entries:
            # No duplicates found - need to show this in a window
            def show_no_duplicates(page: ft.Page):
                page.title = "No Duplicates"
                page.window_width = 400
                page.window_height = 200
                page.add(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE,
                                    color=ft.Colors.GREEN,
                                    size=64,
                                ),
                                ft.Text(
                                    "No duplicate groups found!",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        expand=True,
                    )
                )

            ft.app(target=show_no_duplicates)
            return

        # Flatten all duplicate files into a single list with group separators
        all_photos = []
        for i, (file_hash, photo_files) in enumerate(duplicate_entries):
            all_photos.extend(photo_files)
            # Add a separator marker between groups (except for the last group)
            if i < len(duplicate_entries) - 1:
                all_photos.append(None)  # None represents a separator

        self.open_photos_thumbnail_grid(all_photos)

    def create_thumbnail_image(self, photo_path, thumb_size=(200, 200)):
        """
        Create a base64-encoded thumbnail image for display in Flet.

        Args:
            photo_path (str): Path to the photo file
            thumb_size (tuple): Size of the thumbnail (width, height)

        Returns:
            str: Base64-encoded image data or None if error
        """
        try:
            with Image.open(photo_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Create thumbnail while preserving aspect ratio
                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)

                # Convert to base64 for Flet
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.read()).decode()

                return img_base64

        except Exception as e:
            print(f"Error creating thumbnail for {photo_path}: {e}")
            return None

    def open_photos_thumbnail_grid(self, photo_files):
        """
        Opens all photos in a thumbnail grid using Flet.
        Click on any thumbnail to open the full-size image.
        Click the delete button to remove a photo (with confirmation).
        """
        if not photo_files:
            print("No photos to open.")
            return

        num_photos = len([f for f in photo_files if f is not None])
        print(f"Creating thumbnail grid for {num_photos} photos...")

        def main(page: ft.Page):
            page.title = "Photo Duplicate Viewer - Manage Duplicates"
            page.window_width = 1600
            page.window_height = 900
            page.padding = 20
            page.scroll = ft.ScrollMode.AUTO

            def refresh_grid():
                """Refresh the entire grid after deletion."""
                page.clean()
                # Rebuild the grid with updated data
                self.show_duplicates_grid()

            def open_full_size(path):
                """Open image in system default viewer."""
                subprocess.Popen(
                    ["xdg-open", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            # Instructions at the top
            instructions = ft.Container(
                content=ft.Text(
                    "Click on any thumbnail to open the full-size image. "
                    "Click the delete button (🗑️) to remove a photo.",
                    size=14,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.padding.only(bottom=20),
            )

            # Create grid of thumbnails
            grid_items = []
            current_row = []

            for photo_path in photo_files:
                if photo_path is None:  # Separator
                    # Add current row if it has items
                    if current_row:
                        grid_items.append(ft.Row(current_row, spacing=10, wrap=False))
                        current_row = []

                    # Add separator
                    grid_items.append(
                        ft.Container(
                            content=ft.Divider(thickness=2, color=ft.Colors.RED_400),
                            margin=ft.margin.symmetric(vertical=20),
                        )
                    )
                    continue

                if not os.path.exists(photo_path):
                    print(f"Warning: File does not exist: {photo_path}")
                    continue

                # Create thumbnail
                img_base64 = self.create_thumbnail_image(photo_path)

                if img_base64:
                    filename = os.path.basename(photo_path)

                    # Create thumbnail card
                    thumbnail_card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    # Image with click handler
                                    ft.GestureDetector(
                                        content=ft.Image(
                                            src_base64=img_base64,
                                            width=200,
                                            height=200,
                                            fit=ft.ImageFit.CONTAIN,
                                            border_radius=ft.border_radius.all(8),
                                        ),
                                        on_tap=lambda e, path=photo_path: open_full_size(
                                            path
                                        ),
                                        mouse_cursor=ft.MouseCursor.CLICK,
                                    ),
                                    # Filename
                                    ft.Container(
                                        content=ft.Text(
                                            filename,
                                            size=12,
                                            max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        width=200,
                                        padding=5,
                                    ),
                                    # Delete button
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color=ft.Colors.WHITE,
                                        bgcolor=ft.Colors.RED_600,
                                        tooltip="Delete this photo",
                                        on_click=lambda e, path=photo_path: self.delete_photo_with_confirmation(
                                            path, page, refresh_grid
                                        ),
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=5,
                            ),
                            padding=10,
                        ),
                        elevation=2,
                    )

                    current_row.append(thumbnail_card)

                    # Create new row after 4 items
                    if len(current_row) >= 4:
                        grid_items.append(ft.Row(current_row, spacing=10, wrap=False))
                        current_row = []

                else:
                    # Error placeholder
                    error_card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Icon(
                                        ft.Icons.ERROR, color=ft.Colors.RED, size=64
                                    ),
                                    ft.Text(
                                        f"Error loading:\n{os.path.basename(photo_path)}",
                                        size=12,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            width=220,
                            height=240,
                            padding=10,
                        ),
                        elevation=2,
                    )
                    current_row.append(error_card)

                    if len(current_row) >= 4:
                        grid_items.append(ft.Row(current_row, spacing=10, wrap=False))
                        current_row = []

            # Add remaining items in the last row
            if current_row:
                grid_items.append(ft.Row(current_row, spacing=10, wrap=False))

            # Add all components to page
            page.add(
                instructions,
                ft.Column(
                    grid_items,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )

            print(
                "Thumbnail grid created! Click on any image to open it full-size. "
                "Click the delete button to remove photos."
            )

        ft.app(target=main)

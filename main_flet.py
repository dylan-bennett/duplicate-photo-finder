import flet as ft

from PhotoDuplicateFinderAppFlet import PhotoDuplicateFinderAppFlet


def main(page: ft.Page):
    """Main entry point for the Photo Duplicate Finder Flet app."""
    PhotoDuplicateFinderAppFlet(page)


if __name__ == "__main__":
    ft.app(target=main)


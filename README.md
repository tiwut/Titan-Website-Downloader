# Titan Website Downloader

A modern, high-speed tool for archiving websites locally. Built with Python and CustomTkinter, it features a sleek interface and powerful multi-threaded downloading capabilities.

## Features

- **Self-Contained:** Everything is bundled within the Flatpak; no need to install Python libraries manually.
- **Modern UI:** Automatically adapts to your system's light or dark mode.
- **Parallel Downloading:** Uses multi-threaded downloading for images, scripts, and stylesheets.
- **Deep CSS Scanning:** Automatically detects and downloads web fonts and assets linked within CSS files.

## Installation (Flatpak)

To build and install the application as a Flatpak, follow these steps:

### 1\. Build & Install

flatpak-builder --user --install --force-clean build-dir org.tiwut.TitanDownloader.yml

### 2\. Troubleshooting: Missing Runtimes

If the build fails with an error stating that org.freedesktop.Platform//23.08 or the SDK was not found, you must install the required runtimes manually:

flatpak install flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08

### 3\. Run the App

flatpak run org.tiwut.TitanDownloader

## Manual Development

If you want to run or modify the source code directly:

- Set up a virtual environment: python3 -m venv venv && source venv/bin/activate
- Install dependencies: pip install requests beautifulsoup4 customtkinter
- Run: python3 main.py

### 4\. License

This project is licensed under the MIT License.
This project was developed by Tiwut; the project belongs to the Tiwut Titan Project.

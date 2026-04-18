import os
import re
import requests
import threading
import concurrent.futures
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class WebClonerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Titan Website Downloader")
        self.geometry("700x550")
        self.minsize(600, 500)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.url_label = ctk.CTkLabel(self, text="Target Website URL:", font=("Segoe UI", 14, "bold"))
        self.url_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        self.url_entry = ctk.CTkEntry(self, placeholder_text="https://example.com", width=400)
        self.url_entry.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.url_entry.insert(0, "https://")
        self.folder_label = ctk.CTkLabel(self, text="Save Destination:", font=("Segoe UI", 14, "bold"))
        self.folder_label.grid(row=2, column=0, padx=20, pady=(5, 5), sticky="w")
        self.folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.folder_frame.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.folder_frame.grid_columnconfigure(0, weight=1)
        self.folder_path = ctk.StringVar()
        self.folder_entry = ctk.CTkEntry(self.folder_frame, textvariable=self.folder_path, state="disabled")
        self.folder_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.browse_btn = ctk.CTkButton(self.folder_frame, text="Browse...", width=100, command=self.browse_folder)
        self.browse_btn.grid(row=0, column=1)
        self.log_box = ctk.CTkTextbox(self, state="disabled", wrap="word", font=("Consolas", 12))
        self.log_box.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame)
        self.progress_bar.grid(row=0, column=0, padx=(0, 20), sticky="ew")
        self.progress_bar.set(0)
        self.start_btn = ctk.CTkButton(self.bottom_frame, text="Start Download", font=("Segoe UI", 14, "bold"), command=self.start_cloning_thread)
        self.start_btn.grid(row=0, column=1)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Save Destination")
        if folder:
            self.folder_path.set(folder)

    def log(self, message):
        """Thread-safe UI logging"""
        self.after(0, self._log_insert, message)

    def _log_insert(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def update_progress(self, current, total):
        """Thread-safe progress bar update"""
        if total > 0:
            self.after(0, self.progress_bar.set, current / total)

    def start_cloning_thread(self):
        url = self.url_entry.get().strip()
        base_folder = self.folder_path.get().strip()

        if not url.startswith(("http://", "https://")):
            messagebox.showerror("Error", "Please enter a valid URL starting with http:// or https://")
            return
        if not base_folder:
            messagebox.showerror("Error", "Please select a destination folder.")
            return

        self.start_btn.configure(state="disabled", text="Downloading...")
        self.progress_bar.set(0)
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.log("Initializing clone process...")
        
        threading.Thread(target=self.clone_website, args=(url, base_folder), daemon=True).start()

    def clone_website(self, url, base_folder):
        try:
            self.log(f"Fetching main page: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            parsed_url = urlparse(url)
            resources_to_download = set()

            self.log("Scanning HTML for resources...")
            tags = [('img', 'src'), ('link', 'href'), ('script', 'src')]
            for tag, attr in tags:
                for element in soup.find_all(tag):
                    link = element.get(attr)
                    if link:
                        abs_link = urljoin(url, link)
                        if not abs_link.startswith('data:') and not abs_link.startswith('#'):
                            resources_to_download.add(abs_link)

            css_links = [res for res in resources_to_download if res.endswith('.css') or '.css?' in res]
            if css_links:
                self.log(f"Deep scanning {len(css_links)} CSS files for fonts and images...")
                for css_url in css_links:
                    try:
                        css_res = self.session.get(css_url, timeout=5)
                        urls_in_css = re.findall(r'url\((?:[\'"]?)(.*?)(?:[\'"]?)\)', css_res.text)
                        for css_asset in urls_in_css:
                            if not css_asset.startswith('data:'):
                                abs_css_asset = urljoin(css_url, css_asset)
                                resources_to_download.add(abs_css_asset)
                    except Exception as e:
                        self.log(f"Warning: Could not parse CSS {css_url} - {str(e)}")

            domain = parsed_url.netloc
            page_path = parsed_url.path if parsed_url.path and parsed_url.path != "/" else "/index.html"
            if not os.path.splitext(page_path)[1]:
                page_path += ".html"
                
            local_html_dir = os.path.join(base_folder, domain, os.path.dirname(page_path).lstrip('/'))
            os.makedirs(local_html_dir, exist_ok=True)
            local_html_path = os.path.join(local_html_dir, os.path.basename(page_path))
            
            with open(local_html_path, "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            self.log(f"Saved main HTML to {local_html_path}")
            total_resources = len(resources_to_download)
            self.log(f"Found {total_resources} background resources. Starting parallel download...")

            completed = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_url = {executor.submit(self.download_file, res_url, base_folder): res_url for res_url in resources_to_download}
                
                for future in concurrent.futures.as_completed(future_to_url):
                    res_url = future_to_url[future]
                    completed += 1
                    self.update_progress(completed, total_resources)
                    
                    try:
                        success, filepath = future.result()
                        if success:
                            self.log(f"[{completed}/{total_resources}] Downloaded: {os.path.basename(filepath)}")
                        else:
                            self.log(f"[{completed}/{total_resources}] Skipped/Cached: {os.path.basename(filepath)}")
                    except Exception as e:
                        self.log(f"[{completed}/{total_resources}] Failed: {res_url} -> {str(e)}")

            self.log("\n--- Download Complete! ---")
            self.after(0, lambda: messagebox.showinfo("Success", "Website cloning completed successfully!"))

        except Exception as e:
            self.log(f"\nCRITICAL ERROR: {str(e)}")
            self.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{str(e)}"))
        
        finally:
            self.after(0, lambda: self.start_btn.configure(state="normal", text="Start Download"))

    def download_file(self, url, base_folder):
        """Downloads a single file. Returns (success_bool, filepath). Designed to run in a thread."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path

        if not path or path == "/":
            return False, url

        clean_path = path.lstrip('/')
        local_dir = os.path.join(base_folder, domain, os.path.dirname(clean_path))
        local_filename = os.path.basename(clean_path)
        local_filename = local_filename.split('?')[0].split('#')[0]
        if not local_filename:
            local_filename = "index.html"
            
        local_filepath = os.path.join(local_dir, local_filename)

        os.makedirs(local_dir, exist_ok=True)

        if not os.path.exists(local_filepath):
            response = self.session.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(local_filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True, local_filepath
            else:
                raise Exception(f"HTTP Status {response.status_code}")
        
        return False, local_filepath

if __name__ == "__main__":
    app = WebClonerApp()
    app.mainloop()

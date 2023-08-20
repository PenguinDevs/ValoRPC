:: Hello future me if you are deploying a new update.
:: 1. Change the version in /info.json.
:: 2. Run /build.bat.
:: 3. Run /dist/update_ifp_f.py to update the .ifp file 'files' content.
:: 4. Change the version in general > product version.
:: 5. Change the version in the name of the build > build > setup file path.
:: 6. Run build (begin creating the installer).
:: 7. Run the setup and test the build.
:: 8. Draft a new release https://github.com/PenguinDevs/ValoRPC/releases/new.
:: 9. See example release here https://github.com/PenguinDevs/ValoRPC/releases/edit/v0.2.1-alpha (use this as a template).
:: 10. Create new tag with the name of the version
:: 11. Target the most recent commit (i.e. the commit of this update)
:: 12. Upload setup installer.
:: 13. Publish release
:: 14. Run /version_reset.ps1
:: 15. Open ValoRPC.exe (from wherever it is installed)
:: 16. Continue to update
:: 17. Test again.
:: 18. Done.

pyinstaller vrpc.py --icon=favicon.ico --name="ValoRPC" --noconsole --noconfirm --add-data "info.json;." --add-data "Tesseract-OCR;Tesseract-OCR" --add-data "favicon.ico;." --add-data "ValoRPC Web Downloader.exe;."
PAUSE
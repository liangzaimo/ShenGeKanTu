@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install -U -r requirements.txt pyinstaller
if not exist FreeImage.dll (
  echo Downloading FreeImage.dll ...
  powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; try { Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/imageio/imageio-binaries/master/freeimage/FreeImage-3.18.0-win64.dll' -OutFile 'FreeImage.dll' } catch { Write-Host 'FreeImage.dll download failed, rare formats will not open:' $_.Exception.Message }"
)
python kantu.py --make-icon
python -m PyInstaller --noconfirm --clean --windowed --name ShenGeKanTu --icon kantu.ico --version-file version_info.txt --hidden-import pillow_heif --hidden-import rawpy --collect-all rapidocr_onnxruntime --collect-all easyofd --collect-all reportlab --collect-all pymupdf kantu.py
python kantu.py --write-help dist\ShenGeKanTu
copy /y kantu.ico dist\ShenGeKanTu\ >nul
copy /y LICENSE dist\ShenGeKanTu\LICENSE.txt >nul
if exist FreeImage.dll copy /y FreeImage.dll dist\ShenGeKanTu\ >nul
echo.
echo Done: dist\ShenGeKanTu\ShenGeKanTu.exe
pause

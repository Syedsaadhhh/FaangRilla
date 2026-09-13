$env:Path = "C:\Users\AHSAN\.local\bin;$env:Path"
cd C:\Users\AHSAN\Documents\FaangRilla_Work\backend
uv export --format requirements-txt --output-file requirements.txt
if (Test-Path lambda_dist) { Remove-Item -Recurse -Force lambda_dist }
New-Item -ItemType Directory -Force -Path lambda_dist
uv pip install -r requirements.txt --target lambda_dist
Copy-Item -Path src\opendoor_relay -Destination lambda_dist\opendoor_relay -Recurse
cd lambda_dist
Compress-Archive -Path * -DestinationPath ..\..\infra\backend.zip -Force

@echo off
REM Quick Deployment Package Creator for Windows
REM This creates a deployment package ready for FileZilla/WinSCP upload

echo ========================================
echo Freqtrade Future - Deployment Package
echo ========================================
echo.

REM Create deployment folder
set DEPLOY_DIR=deploy-package
if exist %DEPLOY_DIR% rmdir /s /q %DEPLOY_DIR%
mkdir %DEPLOY_DIR%

echo [1/5] Creating deployment directory...
mkdir %DEPLOY_DIR%\backend
mkdir %DEPLOY_DIR%\frontend
mkdir %DEPLOY_DIR%\frontend\src
mkdir %DEPLOY_DIR%\frontend\public
mkdir %DEPLOY_DIR%\user_data

echo [2/5] Copying backend files...
copy backend\app.py %DEPLOY_DIR%\backend\
copy backend\requirements.txt %DEPLOY_DIR%\backend\
copy backend\Dockerfile %DEPLOY_DIR%\backend\
copy backend\.env %DEPLOY_DIR%\backend\

echo [3/5] Copying frontend files...
xcopy /s /e /y frontend\src %DEPLOY_DIR%\frontend\src\
xcopy /s /e /y frontend\public %DEPLOY_DIR%\frontend\public\
copy frontend\package.json %DEPLOY_DIR%\frontend\
copy frontend\package-lock.json %DEPLOY_DIR%\frontend\
copy frontend\next.config.ts %DEPLOY_DIR%\frontend\
copy frontend\tsconfig.json %DEPLOY_DIR%\frontend\
copy frontend\postcss.config.mjs %DEPLOY_DIR%\frontend\
copy frontend\components.json %DEPLOY_DIR%\frontend\
copy frontend\Dockerfile %DEPLOY_DIR%\frontend\
copy frontend\.env.production %DEPLOY_DIR%\frontend\

echo [4/5] Copying configuration files...
copy docker-compose.full.yml %DEPLOY_DIR%\
copy user_data\config_futures.json %DEPLOY_DIR%\user_data\

echo [5/5] Creating deployment instructions...
(
echo =========================================
echo DEPLOYMENT INSTRUCTIONS
echo =========================================
echo.
echo 1. Upload this entire folder to Vultr server:
echo    Location: /root/freqtrade-future/
echo.
echo 2. Use FileZilla/WinSCP:
echo    Host: sftp://141.164.42.93
echo    User: root
echo    Port: 22
echo.
echo 3. After upload, SSH into server and run:
echo    cd /root/freqtrade-future
echo    docker-compose -f docker-compose.full.yml build
echo    docker-compose -f docker-compose.full.yml up -d
echo.
echo 4. Verify deployment:
echo    http://141.164.42.93:3000 - Frontend
echo    http://141.164.42.93:5000/api/health - Backend
echo    http://141.164.42.93:8080 - Freqtrade
echo.
echo =========================================
) > %DEPLOY_DIR%\UPLOAD_INSTRUCTIONS.txt

echo.
echo ========================================
echo Package created successfully!
echo ========================================
echo.
echo Location: %DEPLOY_DIR%\
echo.
echo Next steps:
echo 1. Open FileZilla or WinSCP
echo 2. Connect to 141.164.42.93
echo 3. Upload the entire '%DEPLOY_DIR%' folder contents
echo 4. Follow UPLOAD_INSTRUCTIONS.txt
echo.
echo See MANUAL_DEPLOYMENT.md for detailed guide
echo ========================================

pause
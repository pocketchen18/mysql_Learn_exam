# MySQL 考试练习系统 - 打包脚本 (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "--- 1. 开始构建前端 ---" -ForegroundColor Cyan
Set-Location frontend
if (-not (Test-Path node_modules)) {
    Write-Host "安装前端依赖..."
    npm install
}
Write-Host "构建前端项目..."
npm run build
Set-Location ..

Write-Host "`n--- 2. 开始打包后端 EXE ---" -ForegroundColor Cyan
if (-not (Test-Path .venv)) {
    Write-Host "未找到虚拟环境，请确保已安装 pyinstaller 和 backend/requirements.txt 中的依赖。" -ForegroundColor Yellow
} else {
    Write-Host "使用虚拟环境进行打包..."
}

# 运行 PyInstaller
pyinstaller --clean "MySQL考试练习系统.spec"

Write-Host "`n--- 3. 整理发布包 ---" -ForegroundColor Cyan
$ReleaseDir = "release"
if (Test-Path $ReleaseDir) { Remove-Item -Recurse -Force $ReleaseDir }
New-Item -ItemType Directory -Path $ReleaseDir

# 复制生成的 EXE
Copy-Item "dist/MySQL考试练习系统.exe" -Destination $ReleaseDir/

# 复制必要的外部资源 (如果 spec 中没有包含，或者需要单独放外面)
# 根据 spec 文件，资源已经被打包进 EXE 了，但为了保险，我们可以把题库也放一份在外面
Copy-Item -Recurse "question_bank" -Destination $ReleaseDir/
Copy-Item "使用说明.txt" -Destination $ReleaseDir/

Write-Host "`n--- 打包完成！ ---" -ForegroundColor Green
Write-Host "发布包位于: $PWD/$ReleaseDir"
Write-Host "你可以将该文件夹压缩为 ZIP 文件并上传到 GitHub Release。"

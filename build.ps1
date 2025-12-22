param (
    [switch] $SkipBuild
)

$outFolder = "entrabulker"
$projRoot = (pwd).path

mkdir ".\$outFolder" -ea 0
mkdir ".\$outFolder\apps" -ea 0
rm ".\$outFolder\apps\$fileName.exe" -ea 0

$mainReact = "01-bulker-app"
$updaterReact = "02-updater-app"

# main app packaging
if(!($skipBuild)){
    cd "$mainReact"
    npm run build

    cd "$projRoot"

    mv "$mainReact\dist" ".\$outFolder\apps\madist" # madist is the main dist folder name
}

$fileName = "EntraBulker"
pyinstaller --onefile --noconsole --name "$fileName" ".\backend\main.py"

mv ".\dist\$fileName.exe" ".\$outFolder\apps\$fileName.exe" -force
rmdir ".\dist" -ea 0

# updater app packaging
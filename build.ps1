param (
    [switch] $SkipMainBuild,
    [switch] $SkipMainApp,
    [switch] $SkipUpdaterBuild,
    [switch] $SkipUpdaterApp
)

$outFolder = "entrabulker"
$projRoot = (pwd).path

rm -recurse ".\$outFolder" -ea 0
mkdir ".\$outFolder" -ea 0
mkdir ".\$outFolder\apps" -ea 0

$mainReact = "01-bulker-app"
$updaterReact = "02-updater-app"

# main app packaging
if(!($SkipMainBuild)){
    cd "$mainReact"

    if(!(test-path "node_modules")){
        npm install
    }
    npm run build

    cd "$projRoot"

    mv "$mainReact\dist" ".\$outFolder\apps\madist" # madist is the main dist folder name
}
if(!($SkipMainApp)){
    $fileName = "EntraBulker"
    pyinstaller --onefile --noconsole --name "$fileName" ".\backend\main.py"

    mv ".\dist\$fileName.exe" ".\$outFolder\apps\$fileName.exe" -force
    rmdir ".\dist" -ea 0
}

# updater app packaging
# all updater contents will be in the parent folder from the root (apps)
if(!($SkipUpdaterBuild)){
    cd "$updaterReact"

    if(!(test-path "node_modules")){
        npm install
    }
    npm run build

    cd "$projRoot"
    mv "$updaterReact\dist" ".\$outFolder\udist" # udist is the updater dist folder name
}

if(!($SkipUpdaterApp)){
    $fileName = "EntraUpdater"
    pyinstaller --onefile --noconsole --name "$fileName" ".\backend\updater_main.py"

    mv ".\dist\$fileName.exe" ".\$outFolder\$fileName.exe" -force
    rmdir ".\dist" -ea 0
}
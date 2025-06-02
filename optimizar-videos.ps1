# Script para comprimir videos existentes a múltiples calidades
# Ejecutar solo si tienes FFmpeg instalado

# Configuración
$inputFolder = "ruta\a\tus\videos\originales"
$outputFolder = "ruta\a\videos\comprimidos" 

# Crear carpetas si no existen
New-Item -ItemType Directory -Force -Path "$outputFolder\1080p"
New-Item -ItemType Directory -Force -Path "$outputFolder\720p"
New-Item -ItemType Directory -Force -Path "$outputFolder\480p"
New-Item -ItemType Directory -Force -Path "$outputFolder\360p"

# Configuraciones de calidad
$qualities = @{
    "1080p" = @{
        "scale" = "1920:1080"
        "bitrate" = "4000k"
        "audio" = "192k"
    }
    "720p" = @{
        "scale" = "1280:720"
        "bitrate" = "2500k"
        "audio" = "128k"
    }
    "480p" = @{
        "scale" = "854:480"
        "bitrate" = "1200k"
        "audio" = "96k"
    }
    "360p" = @{
        "scale" = "640:360"
        "bitrate" = "800k"
        "audio" = "64k"
    }
}

Write-Host "🎬 SugoiAnime - Optimizador de Videos" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Verificar si FFmpeg está instalado
try {
    $ffmpegVersion = ffmpeg -version 2>$null
    Write-Host "✅ FFmpeg encontrado" -ForegroundColor Green
}
catch {
    Write-Host "❌ FFmpeg no encontrado. Instala FFmpeg primero:" -ForegroundColor Red
    Write-Host "   https://ffmpeg.org/download.html" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit
}

# Obtener todos los archivos de video
$videoFiles = Get-ChildItem -Path $inputFolder -Include *.mp4,*.mkv,*.avi,*.mov -Recurse

if ($videoFiles.Count -eq 0) {
    Write-Host "❌ No se encontraron archivos de video en: $inputFolder" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit
}

Write-Host "📁 Encontrados $($videoFiles.Count) archivos de video" -ForegroundColor Cyan

foreach ($video in $videoFiles) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($video.Name)
    
    Write-Host "📽️  Procesando: $($video.Name)" -ForegroundColor Yellow
    
    foreach ($quality in $qualities.Keys) {
        $outputPath = "$outputFolder\$quality\$baseName`_$quality.mp4"
        
        # Saltar si ya existe
        if (Test-Path $outputPath) {
            Write-Host "   ⏭️  $quality ya existe, saltando..." -ForegroundColor Gray
            continue
        }
        
        $config = $qualities[$quality]
        
        Write-Host "   🔄 Generando $quality..." -ForegroundColor Cyan
        
        # Comando FFmpeg optimizado para velocidad y calidad
        $ffmpegArgs = @(
            "-i", $video.FullName,
            "-vf", "scale=$($config.scale)",
            "-c:v", "libx264",
            "-preset", "medium",
            "-b:v", $config.bitrate,
            "-c:a", "aac",
            "-b:a", $config.audio,
            "-movflags", "+faststart",
            "-y",
            $outputPath
        )
        
        try {
            $process = Start-Process -FilePath "ffmpeg" -ArgumentList $ffmpegArgs -Wait -NoNewWindow -PassThru
            
            if ($process.ExitCode -eq 0) {
                $originalSize = [math]::Round((Get-Item $video.FullName).Length / 1MB, 2)
                $newSize = [math]::Round((Get-Item $outputPath).Length / 1MB, 2)
                $savings = [math]::Round((($originalSize - $newSize) / $originalSize) * 100, 1)
                
                Write-Host "   ✅ $quality completado - $originalSize MB → $newSize MB (-$savings%)" -ForegroundColor Green
            } else {
                Write-Host "   ❌ Error procesando $quality" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "   ❌ Error ejecutando FFmpeg: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
}

Write-Host "🎉 ¡Optimización completada!" -ForegroundColor Green
Write-Host "📊 Resultados guardados en: $outputFolder" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Próximos pasos:" -ForegroundColor Yellow
Write-Host "   1. Subir los videos optimizados a tu S3" -ForegroundColor White
Write-Host "   2. Actualizar las URLs en tu base de datos" -ForegroundColor White
Write-Host "   3. Configurar múltiples calidades en el player" -ForegroundColor White

Read-Host "Presiona Enter para salir"

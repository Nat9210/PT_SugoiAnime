/**
 * S3 Video Player Optimizer
 * Optimizaciones específicas para reproducción de videos desde Amazon S3
 */
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar el reproductor Plyr si existe
    if (document.getElementById('player') && typeof Plyr !== 'undefined') {
        const player = new Plyr('#player', {
            controls: [
                'play-large', 'play', 'progress', 'current-time', 'mute', 
                'volume', 'settings', 'pip', 'airplay', 'fullscreen'
            ],
            settings: ['quality', 'speed'],
            seekTime: 10,
            ratio: '16:9',
            // Optimizaciones de rendimiento
            autoplay: false,
            preload: 'metadata',
            storage: { enabled: true, key: 'sugoianime_plyr' },
            quality: {
                default: 720,
                options: [1080, 720, 480, 360],
                forced: true,
                onChange: function(quality) {
                    console.log(`Cambiando calidad a: ${quality}p`);
                    applyQualitySettings(quality);
                    localStorage.setItem('sugoianime_manual_quality', 'true');
                    localStorage.setItem('sugoianime_preferred_quality', quality);
                }
            },
            speed: {
                selected: 1,
                options: [0.5, 0.75, 1, 1.25, 1.5, 2]
            },
            i18n: {
                play: 'Reproducir',
                pause: 'Pausar',
                mute: 'Silenciar',
                unmute: 'Activar sonido',
                fullscreen: 'Pantalla completa',
                settings: 'Ajustes',
                pip: 'Imagen en imagen',
                airplay: 'AirPlay',
                speed: 'Velocidad',
                quality: 'Calidad',
            },
            tooltips: { controls: true, seek: true },
            hideControls: false,
            resetOnEnd: false,
            disableContextMenu: true,
        });
        
        // Configuraciones de calidad para S3
        function applyQualitySettings(quality) {
            const video = document.querySelector('#player video') || document.querySelector('#player');
            if (!video) return;
            
            const currentTime = video.currentTime;
            const wasPlaying = !video.paused;
            
            // Configuraciones por calidad
            const qualitySettings = {
                1080: { bufferSize: 30, preload: 'metadata' },
                720: { bufferSize: 25, preload: 'metadata' },
                480: { bufferSize: 20, preload: 'auto' },
                360: { bufferSize: 15, preload: 'auto' }
            };
            
            const settings = qualitySettings[quality] || qualitySettings[720];
            video.preload = settings.preload;
            
            // Indicador visual de cambio de calidad
            updateQualityDisplay(quality);
            
            console.log(`Calidad aplicada: ${quality}p`);
        }
        
        // Actualizar indicador visual de calidad
        function updateQualityDisplay(quality, showNotification = true) {
            const videoContainer = document.querySelector('.plyr__video-outer');
            if (videoContainer) {
                videoContainer.classList.add('plyr--quality-changing');
                setTimeout(() => {
                    videoContainer.classList.remove('plyr--quality-changing');
                }, 2000);
            }
            
            // Actualizar badge del botón de configuración
            const settingsButton = document.querySelector('.plyr__control--settings');
            if (settingsButton) {
                settingsButton.setAttribute('data-quality', quality + 'p');
                settingsButton.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    settingsButton.style.transform = 'scale(1)';
                }, 300);
            }
            
            // Notificación visual
            if (showNotification) {
                showQualityNotification(quality);
            }
        }
        
        // Mostrar notificación de calidad
        function showQualityNotification(quality) {
            const existingNotification = document.querySelector('.quality-notification');
            if (existingNotification) {
                existingNotification.remove();
            }
            
            const notification = document.createElement('div');
            notification.className = 'quality-notification';
            notification.innerHTML = `
                <i class="fa fa-video"></i>
                <span>Calidad: ${quality}p</span>
            `;
            
            notification.style.cssText = `
                position: absolute;
                top: 20px;
                right: 20px;
                background: rgba(139, 69, 255, 0.9);
                color: white;
                padding: 12px 18px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                z-index: 1000;
                animation: slideInRight 0.3s ease-out, fadeOut 0.3s ease-out 3s forwards;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
                display: flex;
                align-items: center;
                gap: 8px;
                min-width: 150px;
            `;
            
            const playerContainer = document.querySelector('.plyr__video-outer');
            if (playerContainer) {
                playerContainer.style.position = 'relative';
                playerContainer.appendChild(notification);
            }
            
            setTimeout(() => {
                if (notification && notification.parentNode) {
                    notification.remove();
                }
            }, 3500);
        }
        
        // Optimización de buffer
        player.on('progress', function() {
            const buffered = player.buffered;
            const currentTime = player.currentTime;
            
            if (buffered > currentTime + 30) {
                console.log('Buffer optimizado: suficiente contenido descargado');
            }
        });        // Detección de problemas de red
        let lastPlayPos = 0;
        let currentPlayPos = 0;
        let bufferingDetected = false;
        
        const videoElement = document.querySelector('#player video') || document.querySelector('#player');
        const checkBuffering = setInterval(function() {
            if (!videoElement) return;
            
            currentPlayPos = videoElement.currentTime;
            
            // Comprobar si el video está en buffer
            const offset = 1;
            if (!bufferingDetected && currentPlayPos < (lastPlayPos + offset) && !videoElement.paused) {
                videoElement.closest('.plyr__video-outer').classList.add('plyr--buffering');
                bufferingDetected = true;
                console.log("Buffering...");
            }
            
            // Comprobar si el video ha superado el buffer
            if (bufferingDetected && currentPlayPos > (lastPlayPos + offset) && !videoElement.paused) {
                videoElement.closest('.plyr__video-outer').classList.remove('plyr--buffering');
                bufferingDetected = false;
                console.log("No longer buffering...");
            }
            
            lastPlayPos = currentPlayPos;
        }, 500);        // Limpiar el intervalo cuando el video termina
        player.on('ended', function() {
            clearInterval(checkBuffering);
        });
        
        // Mejorar las interacciones con el video
        player.on('enterfullscreen', () => {
            document.querySelector('.plyr__video-outer').classList.add('plyr-fadein');
        });
          player.on('exitfullscreen', () => {
            document.querySelector('.plyr__video-outer').classList.remove('plyr-fadein');
        });
        
        // Detectar errores de reproducción
        player.on('error', function(event) {
            console.error('Error de reproducción:', event);
            const videoContainer = document.querySelector('.plyr__video-outer');
            
            // Mostrar mensaje de error amigable
            const errorMessage = document.createElement('div');
            errorMessage.className = 'video-error-message';
            errorMessage.innerHTML = `
                <h4>Error al reproducir el video</h4>
                <p>Por favor, inténtalo nuevamente o contacta al administrador.</p>
                <button class="btn btn-sm btn-primary" onclick="location.reload()">Reintentar</button>
            `;
            
            if (videoContainer) {
                videoContainer.appendChild(errorMessage);
            }        });
          // Agregar metadatos para la compatibilidad con S3
        player.on('ready', function() {
            console.log('Reproductor listo');
        });
        
        console.log('S3 Video Player inicializado correctamente');
    }
});

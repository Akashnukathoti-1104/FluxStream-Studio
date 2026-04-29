document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.querySelector('[data-upload-input]');
    if (fileInput) {
        const dropzone = fileInput.closest('.dropzone');
        const label = dropzone ? dropzone.querySelector('p') : null;
        const heading = dropzone ? dropzone.querySelector('strong') : null;
        const defaultLabel = label ? label.textContent : '';
        const defaultHeading = heading ? heading.textContent : '';

        const updateSelection = (file) => {
            if (heading) {
                heading.textContent = file ? file.name : defaultHeading;
            }
            if (label) {
                label.textContent = file
                    ? `Selected file: ${file.name}`
                    : defaultLabel;
            }
        };

        fileInput.addEventListener('change', () => {
            updateSelection(fileInput.files && fileInput.files[0]);
        });

        if (dropzone) {
            dropzone.addEventListener('dragover', (event) => {
                event.preventDefault();
                dropzone.classList.add('is-dragging');
            });

            dropzone.addEventListener('dragleave', () => {
                dropzone.classList.remove('is-dragging');
            });

            dropzone.addEventListener('drop', (event) => {
                event.preventDefault();
                dropzone.classList.remove('is-dragging');
                if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
                    fileInput.files = event.dataTransfer.files;
                    updateSelection(fileInput.files[0]);
                }
            });
        }
    }

    const player = document.querySelector('[data-hls-url]');
    if (player) {
        const sourceUrl = player.dataset.hlsUrl;
        if (window.Hls && window.Hls.isSupported()) {
            const hls = new window.Hls({
                capLevelToPlayerSize: true,
                startLevel: -1,
            });
            hls.loadSource(sourceUrl);
            hls.attachMedia(player);
            hls.on(window.Hls.Events.ERROR, (_, data) => {
                if (data.fatal) {
                    player.outerHTML = '<div class="state-card failed"><h3>Playback error</h3><p>The browser could not attach the stream. Try refreshing or reprocessing the upload.</p></div>';
                }
            });
        } else if (player.canPlayType('application/vnd.apple.mpegurl')) {
            player.src = sourceUrl;
        }
    }

    document.querySelectorAll('.flash').forEach((flash) => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-6px)';
            flash.style.transition = 'all 240ms ease';
        }, 4200);
    });
});

(function () {
  const video = document.getElementById('player');
  if (!video) return;

  const playlist = video.dataset.playlist;
  const resumeAt = parseInt(video.dataset.resume || '0', 10);

  if (window.Hls && Hls.isSupported() && playlist) {
    const hls = new Hls();
    hls.loadSource(playlist);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, function () {
      if (resumeAt > 0) video.currentTime = resumeAt;
    });
  } else if (playlist) {
    video.src = playlist;
  }

  document.addEventListener('keydown', (event) => {
    if (event.code === 'Space') {
      event.preventDefault();
      video.paused ? video.play() : video.pause();
    }
    if (event.key === 'm') video.muted = !video.muted;
    if (event.key === 'f' && video.requestFullscreen) video.requestFullscreen();
    if (event.key === 'ArrowLeft') video.currentTime = Math.max(0, video.currentTime - 10);
    if (event.key === 'ArrowRight') video.currentTime += 10;
  });
})();

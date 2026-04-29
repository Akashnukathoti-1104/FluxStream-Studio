(function () {
  const form = document.getElementById('uploadForm');
  const output = document.getElementById('uploadProgress');
  const startLive = document.getElementById('startLive');
  const endLive = document.getElementById('endLive');
  const liveOutput = document.getElementById('liveOutput');

  if (form && output) {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const payload = {
        title: form.title.value,
        description: form.description.value,
        category: form.category.value,
        tags: (form.tags.value || '').split(',').map((s) => s.trim()).filter(Boolean),
      };

      const response = await fetch('/api/videos/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!data.job_id) {
        output.textContent = 'Upload request failed.';
        return;
      }

      output.textContent = 'Upload accepted. Waiting for progress...';
      const source = new EventSource('/api/videos/upload/' + data.job_id + '/status');
      source.onmessage = (msg) => {
        const status = JSON.parse(msg.data);
        output.textContent = 'Job ' + status.job_id + ': ' + status.progress + '% (' + status.status + ')';
        if (status.progress >= 100) source.close();
      };
      source.onerror = () => source.close();
    });
  }

  if (startLive && liveOutput) {
    startLive.addEventListener('click', async () => {
      const r = await fetch('/api/live/start', { method: 'POST' });
      liveOutput.textContent = JSON.stringify(await r.json(), null, 2);
    });
  }

  if (endLive && liveOutput) {
    endLive.addEventListener('click', async () => {
      const r = await fetch('/api/live/end', { method: 'POST' });
      liveOutput.textContent = JSON.stringify(await r.json(), null, 2);
    });
  }
})();

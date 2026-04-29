(function () {
  const form = document.getElementById('uploadForm');
  const output = document.getElementById('uploadProgress');
  const videoInput = document.getElementById('videoFile');
  const preview = document.getElementById('uploadPreview');
  const startLive = document.getElementById('startLive');
  const endLive = document.getElementById('endLive');
  const liveOutput = document.getElementById('liveOutput');

  if (videoInput && preview) {
    videoInput.addEventListener('change', () => {
      const file = videoInput.files && videoInput.files[0];
      if (!file) {
        preview.textContent = 'Choose a file to see a preview.';
        return;
      }

      const url = URL.createObjectURL(file);
      preview.innerHTML = '<video controls src="' + url + '"></video>';
    });
  }

  if (form && output) {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const file = form.video && form.video.files && form.video.files[0];
      if (!file) {
        output.textContent = 'Please choose a video file.';
        return;
      }

      const payload = {
        title: form.title.value,
        description: form.description.value,
        category: form.category.value,
        tags: (form.tags.value || '').split(',').map((s) => s.trim()).filter(Boolean),
      };

      // request server for presigned POST fields
      payload.original_filename = file.name;
      const response = await fetch('/api/videos/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!data.job_id || !data.presigned_url) {
        output.textContent = 'Upload request failed.';
        return;
      }

      // build FormData for S3 presigned POST
      const formData = new FormData();
      Object.entries(data.presigned_fields || {}).forEach(([k, v]) => formData.append(k, v));
      formData.append('file', file);

      output.textContent = 'Uploading to S3...';
      const uploadResp = await fetch(data.presigned_url, { method: 'POST', body: formData });
      if (!(uploadResp.status === 204 || (uploadResp.status >= 200 && uploadResp.status < 300))) {
        output.textContent = 'Upload to storage failed.';
        return;
      }

      // notify server that upload is complete so processing can start
      await fetch('/api/videos/upload/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: data.job_id, object_key: data.object_key, file_size: file.size }),
      });

      output.textContent = 'Upload accepted. Waiting for processing progress...';
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

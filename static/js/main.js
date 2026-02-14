document.addEventListener('DOMContentLoaded', function() {
    // Modal Logic
    const modal = document.getElementById('addModal');
    const btn = document.getElementById('addTorrentBtn');
    const span = document.getElementsByClassName("close")[0];

    if(btn) {
        btn.onclick = function() {
            modal.style.display = "flex";
        }
    }

    if(span) {
        span.onclick = function() {
            modal.style.display = "none";
        }
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    // Polling Logic
    function updateStatus() {
        fetch('/api/status/')
            .then(response => response.json())
            .then(data => {
                data.tasks.forEach(task => {
                    const el = document.getElementById('task-' + task.id);
                    if (el) {
                        // Update existing element
                        el.querySelector('.progress-bar').style.width = task.progress + '%';
                        el.querySelector('.torrent-meta span:first-child').innerText = task.progress.toFixed(1) + '%';
                        el.querySelector('.speed-down').innerHTML = `<i class="fa-solid fa-arrow-down"></i> ${(task.download_speed / 1024).toFixed(1)} KB/s`;
                        el.querySelector('.speed-up').innerHTML = `<i class="fa-solid fa-arrow-up"></i> ${(task.upload_speed / 1024).toFixed(1)} KB/s`;
                        el.querySelector('.eta').innerText = 'ETA: ' + task.eta + 's';
                        
                        // Update status class/text
                        const statusEl = el.querySelector('.torrent-status');
                        statusEl.className = 'torrent-status ' + task.status;
                        statusEl.innerText = task.status.charAt(0).toUpperCase() + task.status.slice(1);
                        
                        // Handle completion - maybe remove from list or move to bottom
                    } else {
                        // Reload page to show new tasks or insert dynamically (for now verify via simple reload if missing)
                        // Implementing dynamic insert is complex without a framework, but for now simple polling updates exist is fine.
                    }
                });
            });
    }

    setInterval(updateStatus, 2000);
});

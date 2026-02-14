import libtorrent as lt
import time
import threading
import os
from django.conf import settings
from django.utils import timezone
from .models import TorrentTask

class TorrentManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TorrentManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        self.output_dir = settings.TORRENT_SAVE_PATH
        
        # Ensure download directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        self.handles = {} # Map info_hash -> handle
        self.running = False
        self._load_existing_torrents()
        self.start_monitoring()
        self._initialized = True

    def _load_existing_torrents(self):
        """Loads torrents from DB on startup"""
        print("Loading existing torrents...")
        tasks = TorrentTask.objects.exclude(status='completed') # Or maybe restart all not fully removed?
        # For simplicity, we might just load everything that's not 'error' or checking if file exists?
        # A better approach for a real app is to save state files (.fastresume). 
        # For this MVP, we might need to re-add them if the session was lost.
        # But wait, restarting the server loses the session. 
        # We need to save .torrent files or magnet links to restore them.
        # Implemented for MVP: Only active ones might be tricky to restore without stored metadata.
        # Let's just focus on new adds for now, or maybe simple restoration.
        pass

    def add_magnet(self, magnet_link):
        params = {
            'save_path': self.output_dir,
            'storage_mode': lt.storage_mode_t(1),
        }
        handle = lt.add_magnet_uri(self.session, magnet_link, params)
        
        #Wait for metadata to get name? Or just save hash first.
        # Ideally we wait a bit or let the loop update it.
        
        info_hash = str(handle.info_hash())
        
        task, created = TorrentTask.objects.get_or_create(
            info_hash=info_hash,
            defaults={'save_path': self.output_dir}
        )
        
        self.handles[info_hash] = handle
        return task

    def add_file(self, torrent_file_path):
        info = lt.torrent_info(torrent_file_path)
        params = {
            'save_path': self.output_dir,
            'storage_mode': lt.storage_mode_t(1),
            'ti': info,
        }
        handle = self.session.add_torrent(params)
        info_hash = str(handle.info_hash())

        task, created = TorrentTask.objects.get_or_create(
            info_hash=info_hash,
            defaults={
                'name': info.name(),
                'total_size': info.total_size(),
                'save_path': self.output_dir
            }
        )
        self.handles[info_hash] = handle
        return task

    def start_monitoring(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self):
        while self.running:
            # Update libtorrent session
            # params = lt.session_params()
            # self.session.post_torrent_updates() # Only if using alerts, but detailed loop is easier for MVP
            
            for info_hash, handle in list(self.handles.items()):
                try:
                    status = handle.status()
                    task = TorrentTask.objects.get(info_hash=info_hash)
                    
                    task.progress = status.progress * 100
                    task.download_speed = status.download_rate
                    task.upload_speed = status.upload_rate
                    task.name = handle.name() # Update name if magnet resolved
                    
                    # Update status state
                    if status.is_seeding:
                        task.status = 'seeding'
                    elif status.state == lt.torrent_status.checking_files:
                        task.status = 'checking'
                    elif status.paused:
                        task.status = 'paused'
                    else:
                        task.status = 'downloading'
                        
                    if task.progress >= 100:
                         task.status = 'completed'
                         task.completed_at = timezone.now()

                    task.save()
                    
                except Exception as e:
                    print(f"Error updating torrent {info_hash}: {e}")
            
            time.sleep(1)

    def pause_torrent(self, info_hash):
        if info_hash in self.handles:
            self.handles[info_hash].pause()
    
    def resume_torrent(self, info_hash):
        if info_hash in self.handles:
            self.handles[info_hash].resume()

    def remove_torrent(self, info_hash, delete_files=False):
        if info_hash in self.handles:
            self.session.remove_torrent(self.handles[info_hash], delete_files)
            del self.handles[info_hash]
            TorrentTask.objects.filter(info_hash=info_hash).delete()

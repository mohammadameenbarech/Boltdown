"""
Enhanced Torrent Manager using aria2c
Pure solution - no Python DLL dependencies
Uses aria2c command-line tool for actual downloads
"""

import os
import subprocess
import json
import time
import threading
import hashlib
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
        
        self.output_dir = str(settings.TORRENT_SAVE_PATH)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.aria2_process = None
        self.aria2_secret = os.environ.get('ARIA2_SECRET', 'torrentwebchangeme')
        self.running = False

        
        self._start_aria2()
        self.start_monitoring()
        self._initialized = True
        
        print("[+] TorrentManager initialized with aria2c backend")

    def _start_aria2(self):
        """Start aria2c RPC server"""
        try:
            # Start aria2c in RPC mode
            aria2_cmd = [
                "aria2c",
                "--enable-rpc",
                f"--rpc-secret={self.aria2_secret}",
                "--rpc-listen-port=6800",
                f"--dir={self.output_dir}",
                "--max-connection-per-server=16",
                "--min-split-size=1M",
                "--split=16",
                "--continue=true",
                "--seed-time=0",  # Don't seed after download
                "--bt-max-peers=50"
            ]
            
            self.aria2_process = subprocess.Popen(
                aria2_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,  
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            time.sleep(2)  # Wait for aria2c to start
            print("[+] aria2c RPC server started")
            
        except FileNotFoundError:
            print("[!] aria2c not found!")
            print("[!] Download from: https://github.com/aria2/aria2/releases")
            print("[!] Add to PATH or place in project directory")

    def _aria2_rpc(self, method, params=[]):
        """Call aria2 RPC method"""
        import requests
        
        payload = {
            "jsonrpc": "2.0",
            "id": "torrentweb",
            "method": method,
            "params": [f"token:{self.aria2_secret}"] + params
        }
        
        try:
            response = requests.post("http://localhost:6800/jsonrpc", json=payload)
            result = response.json()
            return result.get('result')
        except:
            return None

    def add_magnet(self, magnet_link):
        """Add magnet link"""
        try:
            # Add to aria2
            gid = self._aria2_rpc("aria2.addUri", [[magnet_link]])
            
            if gid:
                # Extract info hash
                info_hash = self._extract_hash_from_magnet(magnet_link)
                name = self._extract_name_from_magnet(magnet_link) or f"Download_{info_hash[:8]}"
                
                task = TorrentTask.objects.create(
                    info_hash=info_hash or gid,
                    name=name,
                    save_path=self.output_dir,
                    status='downloading'
                )
                
                return task
                
        except Exception as e:
            print(f"[!] Error adding magnet: {e}")
            
        return None

    def add_file(self, torrent_file_path):
        """Add .torrent file"""
        try:
            # Read and encode torrent file
            with open(torrent_file_path, 'rb') as f:
                import base64
                torrent_b64 = base64.b64encode(f.read()).decode()
            
            # Add to aria2
            gid = self._aria2_rpc("aria2.addTorrent", [torrent_b64])
            
            if gid:
                # Get torrent info
                import bencodepy
                with open(torrent_file_path, 'rb') as f:
                    torrent_data = bencodepy.decode(f.read())
                
                info = torrent_data[b'info']
                info_hash = hashlib.sha1(bencodepy.encode(info)).hexdigest()
                name = info.get(b'name', b'Unknown').decode('utf-8', errors='ignore')
                
                task = TorrentTask.objects.create(
                    info_hash=info_hash,
                    name=name,
                    save_path=self.output_dir,
                    status='downloading'
                )
                
                return task
                
        except Exception as e:
            print(f"[!] Error adding torrent: {e}")
            
        return None

    def start_monitoring(self):
        """Monitor downloads"""
        if not self.running:
            self.running = True
            threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self):
        """Update download status"""
        while self.running:
            try:
                # Get all active downloads from aria2
                active = self._aria2_rpc("aria2.tellActive")
                
                if active:
                    for download in active:
                        self._update_task_from_aria2(download)
                
                # Check completed downloads
                stopped = self._aria2_rpc("aria2.tellStopped", [0, 100])
                if stopped:
                    for download in stopped:
                        self._update_task_from_aria2(download)
                        
            except Exception as e:
                print(f"[!] Monitor error: {e}")
            
            time.sleep(2)

    def _update_task_from_aria2(self, download):
        """Update task from aria2 download info"""
        try:
            info_hash = download.get('infoHash', '')
            
            if not info_hash:
                return
            
            task = TorrentTask.objects.filter(info_hash=info_hash).first()
            if not task:
                return
            
            # Update progress
            total = int(download.get('totalLength', 0))
            completed = int(download.get('completedLength', 0))
            
            if total > 0:
                task.progress = (completed / total) * 100
                task.total_size = total
            
            # Update speeds
            task.download_speed = int(download.get('downloadSpeed', 0))
            task.upload_speed = int(download.get('uploadSpeed', 0))
            
            # Update status
            status = download.get('status', 'active')
            if status == 'complete':
                task.status = 'completed'
                task.completed_at = timezone.now()
            elif status == 'paused':
                task.status = 'paused'
            elif status == 'error':
                task.status = 'error'
                task.error_message = download.get('errorMessage', 'Unknown error')
            else:
                task.status = 'downloading'
            
            # Update name if not set
            if task.name.startswith('Download_'):
                bittorrent = download.get('bittorrent', {})
                if bittorrent and 'info' in bittorrent:
                    task.name = bittorrent['info'].get('name', task.name)
            
            task.save()
            
        except Exception as e:
            print(f"[!] Error updating task: {e}")

    def pause_torrent(self, info_hash):
        """Pause download"""
        # Find GID from info_hash
        # This is simplified - in production, maintain a mapping
        pass

    def resume_torrent(self, info_hash):
        """Resume download"""
        pass

    def remove_torrent(self, info_hash, delete_files=False):
        """Remove download"""
        try:
            task = TorrentTask.objects.get(info_hash=info_hash)
            task.delete()
            
            if delete_files:
                import shutil
                file_path = os.path.join(self.output_dir, task.name)
                if os.path.exists(file_path):
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        else:
                            shutil.rmtree(file_path)
                    except:
                        pass
        except:
            pass

    def _extract_hash_from_magnet(self, magnet_link):
        try:
            parts = magnet_link.split('&')
            for part in parts:
                if 'xt=urn:btih:' in part:
                    return part.split('xt=urn:btih:')[1].split('&')[0].lower()
        except:
            pass
        return None

    def _extract_name_from_magnet(self, magnet_link):
        from urllib.parse import unquote
        try:
            parts = magnet_link.split('&')
            for part in parts:
                if 'dn=' in part:
                    return unquote(part.split('dn=')[1].split('&')[0])
        except:
            pass
        return None

    def __del__(self):
        """Cleanup"""
        if self.aria2_process:
            self.aria2_process.terminate()

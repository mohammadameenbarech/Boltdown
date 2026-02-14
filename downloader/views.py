from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import TorrentTask
from .services import TorrentManager
import os

def dashboard(request):
    tasks = TorrentTask.objects.all().order_by('-added_at')
    return render(request, 'downloader/index.html', {'tasks': tasks})

def add_torrent(request):
    if request.method == 'POST':
        magnet = request.POST.get('magnet_link')
        torrent_file = request.FILES.get('torrent_file')
        
        manager = TorrentManager()
        
        if magnet:
            manager.add_magnet(magnet)
        elif torrent_file:
            # Save temporary file
            save_path = os.path.join(settings.MEDIA_ROOT, 'torrents', torrent_file.name)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb+') as destination:
                for chunk in torrent_file.chunks():
                    destination.write(chunk)
            manager.add_file(save_path)
            
        return redirect('dashboard')
    return redirect('dashboard')

def api_status(request):
    tasks = TorrentTask.objects.all().values(
        'id', 'name', 'progress', 'status', 'download_speed', 'upload_speed', 'eta', 'total_size'
    )
    return JsonResponse({'tasks': list(tasks)})

def control_torrent(request, task_id, action):
    manager = TorrentManager()
    try:
        task = TorrentTask.objects.get(id=task_id)
        if action == 'pause':
            manager.pause_torrent(task.info_hash)
        elif action == 'resume':
            manager.resume_torrent(task.info_hash)
        elif action == 'delete':
            delete_files = request.GET.get('delete_files') == 'true'
            manager.remove_torrent(task.info_hash, delete_files)
    except TorrentTask.DoesNotExist:
        pass
    
    return redirect('dashboard')
